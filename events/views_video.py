from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .models import PromoVideo, ProjectPromoVideo, Event
from .forms import PromoVideoForm, ProjectPromoVideoForm


class PromoVideoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание промо-видео"""
    model = PromoVideo
    form_class = PromoVideoForm
    template_name = 'events/promovideo_form.html'
    
    def test_func(self):
        """Проверка, что пользователь - организатор мероприятия"""
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        return self.request.user == event.organizer or self.request.user.is_staff
    
    def form_valid(self, form):
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        form.instance.event = event
        
        # Если это главное промо, снимаем флаг с других видео
        if form.cleaned_data.get('is_main_promo'):
            PromoVideo.objects.filter(event=event, is_main_promo=True).update(is_main_promo=False)
        
        response = super().form_valid(form)
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'video_id': self.object.id,
                'video_title': self.object.title
            })
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = get_object_or_404(Event, pk=self.kwargs['event_id'])
        return context


class PromoVideoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование промо-видео"""
    model = PromoVideo
    form_class = PromoVideoForm
    template_name = 'events/promovideo_form.html'
    
    def test_func(self):
        video = self.get_object()
        return self.request.user == video.event.organizer or self.request.user.is_staff


class PromoVideoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление промо-видео"""
    model = PromoVideo
    template_name = 'events/promovideo_confirm_delete.html'
    
    def test_func(self):
        video = self.get_object()
        return self.request.user == video.event.organizer or self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('event_detail', kwargs={'pk': self.object.event.pk})


@require_POST
@login_required
def track_video_view(request, video_id):
    """Трекинг просмотров видео"""
    video = get_object_or_404(PromoVideo, id=video_id)
    
    # Проверяем, не просматривал ли пользователь уже это видео
    view_key = f'video_view_{video_id}'
    if not request.session.get(view_key):
        video.increment_view_count()
        request.session[view_key] = True
        request.session.modified = True
    
    return JsonResponse({'success': True, 'view_count': video.view_count})


class AboutProjectView(TemplateView):
    """Страница 'О проекте' с видео"""
    template_name = 'events/about_project.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        project_promos = ProjectPromoVideo.objects.filter(is_active=True)
        
        context.update({
            'project_promos': {
                'main': project_promos.filter(video_type='main'),
                'other': project_promos.exclude(video_type='main')
            }
        })
        return context


@require_POST
def track_project_promo_view(request):
    """Трекинг просмотров промороликов проекта"""
    video_id = request.POST.get('video_id')
    
    if video_id and video_id != '0':
        try:
            video = ProjectPromoVideo.objects.get(id=video_id)
            video.increment_view_count()
            return JsonResponse({'success': True, 'view_count': video.view_count})
        except ProjectPromoVideo.DoesNotExist:
            pass
    
    return JsonResponse({'success': False})
