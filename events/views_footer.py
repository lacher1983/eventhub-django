from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _


class AboutView(TemplateView):
    """Страница 'О нас'"""
    template_name = 'events/footer/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('О компании EventHub'),
            'meta_description': _('EventHub - ведущая платформа для организации и поиска мероприятий. Узнайте больше о нашей миссии, команде и ценностях.'),
        })
        return context

class BlogView(TemplateView):
    """Страница блога"""
    template_name = 'events/footer/blog.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Пример статей блога
        blog_posts = [
            {
                'title': _('Топ 10 трендов мероприятий в 2025 году'),
                'excerpt': _('Исследуем основные тренды в организации мероприятий, которые будут доминировать в 2025 году.'),
                'date': '15 января 2025',
                'author': 'Анна Петрова',
                'read_time': '5 мин',
                'category': _('Тренды'),
            },
            {
                'title': _('Как организовать успешное онлайн-мероприятие'),
                'excerpt': _('Практические советы по организации engaging онлайн-мероприятий от наших экспертов.'),
                'date': '10 января 2025',
                'author': 'Максим Иванов',
                'read_time': '7 мин',
                'category': _('Советы'),
            },
            {
                'title': _('История успеха: TechConf 2024'),
                'excerpt': _('Как мы организовали крупнейшую IT-конференцию года с участием 5000+ участников.'),
                'date': '5 января 2025',
                'author': 'Елена Сидорова',
                'read_time': '8 мин',
                'category': _('Кейсы'),
            },
        ]
        
        context.update({
            'page_title': _('Блог EventHub'),
            'blog_posts': blog_posts,
            'meta_description': _('Читайте последние статьи о мероприятиях, трендах и советы по организации от команды EventHub.'),
        })
        return context

class CareersView(TemplateView):
    """Страница 'Карьера'"""
    template_name = 'events/footer/careers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Пример вакансий
        job_openings = [
            {
                'title': _('Frontend Developer (React)'),
                'department': _('Технологии'),
                'location': _('Москва / Удаленно'),
                'type': _('Полная занятость'),
                'description': _('Разработка пользовательских интерфейсов для нашей платформы мероприятий.'),
            },
            {
                'title': _('Event Manager'),
                'department': _('Операции'),
                'location': _('Москва'),
                'type': _('Полная занятость'),
                'description': _('Организация и координация мероприятий на платформе EventHub.'),
            },
            {
                'title': _('Content Marketing Specialist'),
                'department': _('Маркетинг'),
                'location': _('Удаленно'),
                'type': _('Полная занятость'),
                'description': _('Создание контента для блога и социальных сетей.'),
            },
        ]
        
        context.update({
            'page_title': _('Карьера в EventHub'),
            'job_openings': job_openings,
            'meta_description': _('Присоединяйтесь к команде EventHub! Откройте для себя возможности карьерного роста в быстрорастущем стартапе.'),
        })
        return context

class PressView(TemplateView):
    """Страница 'Пресса'"""
    template_name = 'events/footer/press.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Пример пресс-релизов
        press_releases = [
            {
                'title': _('EventHub привлекает $5M инвестиций для расширения платформы'),
                'date': '20 января 2025',
                'summary': _('EventHub объявляет о завершении раунда финансирования Series A для развития AI-рекомендаций и международной экспансии.'),
                'source': _('TechCrunch'),
            },
            {
                'title': _('Запуск AI-рекомендательной системы мероприятий'),
                'date': '15 декабря 2024',
                'summary': _('EventHub представляет инновационную систему рекомендаций на основе машинного обучения.'),
                'source': _('VC.ru'),
            },
            {
                'title': _('Партнерство с ведущими вузами страны'),
                'date': '1 декабря 2024',
                'summary': _('EventHub запускает образовательную программу для студентов в партнерстве с МГУ и ВШЭ.'),
                'source': _('RB.ru'),
            },
        ]
        
        # Контакты для прессы
        press_contacts = {
            'press_email': 'press@eventhub.ru',
            'press_phone': '+7 (495) 123-45-67',
            'press_contact': _('Мария Иванова, PR-менеджер'),
        }
        
        context.update({
            'page_title': _('Пресс-центр EventHub'),
            'press_releases': press_releases,
            'press_contacts': press_contacts,
            'meta_description': _('Пресс-центр EventHub. Последние новости, пресс-релизы и контакты для СМИ.'),
        })
        return context

class ContactView(TemplateView):
    """Страница 'Контакты'"""
    template_name = 'events/footer/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        contact_info = {
            'general_email': 'hello@eventhub.ru',
            'support_email': 'support@eventhub.ru',
            'phone': '+7 (495) 123-45-67',
            'address': _('Москва, Пресненская наб., 12, ММДЦ "Москва-Сити"'),
            'work_hours': _('Пн-Пт: 9:00-18:00'),
        }
        
        departments = [
            {
                'name': _('Техническая поддержка'),
                'email': 'support@eventhub.ru',
                'phone': '+7 (495) 123-45-68',
                'description': _('Помощь пользователям и решение технических вопросов'),
            },
            {
                'name': _('Отдел мероприятий'),
                'email': 'events@eventhub.ru',
                'phone': '+7 (495) 123-45-69',
                'description': _('Организация и координация мероприятий'),
            },
            {
                'name': _('Партнерства'),
                'email': 'partners@eventhub.ru',
                'phone': '+7 (495) 123-45-70',
                'description': _('Сотрудничество с организаторами и партнерами'),
            },
        ]
        
        context.update({
            'page_title': _('Контакты EventHub'),
            'contact_info': contact_info,
            'departments': departments,
            'meta_description': _('Свяжитесь с командой EventHub. Контакты, адреса и способы связи для разных отделов компании.'),
        })
        return context
    

class HelpCenterView(TemplateView):
    """Центр помощи"""
    template_name = 'events/footer/help_center.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        help_categories = [
            {
                'title': _('Регистрация и аккаунт'),
                'icon': 'fas fa-user-circle',
                'questions': [
                    _('Как зарегистрироваться на платформе?'),
                    _('Как восстановить пароль?'),
                    _('Как изменить данные профиля?'),
                    _('Как удалить аккаунт?'),
                ]
            },
            {
                'title': _('Мероприятия и билеты'),
                'icon': 'fas fa-ticket-alt',
                'questions': [
                    _('Как найти подходящее мероприятие?'),
                    _('Как купить билеты?'),
                    _('Как вернуть билеты?'),
                    _('Где найти электронные билеты?'),
                ]
            },
            {
                'title': _('Организация мероприятий'),
                'icon': 'fas fa-calendar-plus',
                'questions': [
                    _('Как создать мероприятие?'),
                    _('Какие комиссии берет платформа?'),
                    _('Как продвигать мероприятие?'),
                    _('Как управлять регистрациями?'),
                ]
            },
            {
                'title': _('Платежи и безопасность'),
                'icon': 'fas fa-shield-alt',
                'questions': [
                    _('Какие способы оплаты принимаются?'),
                    _('Безопасны ли платежи на платформе?'),
                    _('Как получить возврат средств?'),
                    _('Есть ли скрытые комиссии?'),
                ]
            }
        ]
        
        context.update({
            'page_title': _('Центр помощи'),
            'help_categories': help_categories,
            'meta_description': _('Найдите ответы на часто задаваемые вопросы о работе платформы EventHub. Помощь по регистрации, мероприятиям и оплате.'),
        })
        return context

class PrivacyPolicyView(TemplateView):
    """Политика конфиденциальности"""
    template_name = 'events/footer/privacy_policy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        policy_sections = [
            {
                'title': _('1. Сбор информации'),
                'content': _('Мы собираем информацию, которую вы предоставляете при регистрации, создании мероприятий, покупке билетов и использовании наших услуг. Это включает ваше имя, email, телефон и данные мероприятий.')
            },
            {
                'title': _('2. Использование информации'),
                'content': _('Мы используем вашу информацию для предоставления услуг, улучшения платформы, отправки уведомлений о мероприятиях и обеспечения безопасности.')
            },
            {
                'title': _('3. Защита данных'),
                'content': _('Мы применяем современные методы шифрования и безопасности для защиты ваших данных. Ваша информация хранится на защищенных серверах.')
            },
            {
                'title': _('4. Cookies и отслеживание'),
                'content': _('Мы используем cookies для улучшения пользовательского опыта, аналитики и персонализации контента.')
            },
            {
                'title': _('5. Третьи стороны'),
                'content': _('Мы не продаем ваши данные третьим лицам. Мы можем делиться информацией только с партнерами, необходимыми для предоставления услуг.')
            },
            {
                'title': _('6. Ваши права'),
                'content': _('Вы имеете право на доступ, исправление и удаление ваших данных. Для этого обратитесь в службу поддержки.')
            }
        ]
        
        context.update({
            'page_title': _('Политика конфиденциальности'),
            'policy_sections': policy_sections,
            'meta_description': _('Политика конфиденциальности EventHub. Узнайте, как мы собираем, используем и защищаем ваши персональные данные.'),
        })
        return context

class TermsOfUseView(TemplateView):
    """Условия использования"""
    template_name = 'events/footer/terms_of_use.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        terms_sections = [
            {
                'title': _('1. Общие положения'),
                'content': _('Используя платформу EventHub, вы соглашаетесь с настоящими условиями. Платформа предоставляет услуги по организации и поиску мероприятий.')
            },
            {
                'title': _('2. Регистрация и аккаунт'),
                'content': _('Для использования некоторых функций требуется регистрация. Вы несете ответственность за сохранность данных аккаунта.')
            },
            {
                'title': _('3. Организация мероприятий'),
                'content': _('Организаторы несут ответственность за достоверность информации о мероприятиях. Запрещено создавать мероприятия, нарушающие законодательство.')
            },
            {
                'title': _('4. Покупка билетов'),
                'content': _('Покупка билетов осуществляется через защищенные платежные системы. Возврат средств регулируется правилами организатора.')
            },
            {
                'title': _('5. Интеллектуальная собственность'),
                'content': _('Все материалы платформы защищены авторским правом. Запрещено копировать и распространять контент без разрешения.')
            },
            {
                'title': _('6. Ответственность'),
                'content': _('EventHub не несет ответственности за содержание мероприятий и действия организаторов. Все споры решаются между участниками и организаторами.')
            }
        ]
        
        context.update({
            'page_title': _('Условия использования'),
            'terms_sections': terms_sections,
            'meta_description': _('Условия использования платформы EventHub. Правила регистрации, организации мероприятий и использования сервиса.'),
        })
        return context

class OrganizerSolutionsView(TemplateView):
    """Решения для организаторов"""
    template_name = 'events/footer/organizer_solutions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        solutions = [
            {
                'title': _('Продвинутая аналитика'),
                'icon': 'fas fa-chart-line',
                'description': _('Детальная статистика по регистрациям, продажам и вовлеченности участников'),
                'features': [
                    _('Отслеживание в реальном времени'),
                    _('Демографическая аналитика'),
                    _('Отчеты по продажам'),
                    _('ROI калькулятор')
                ]
            },
            {
                'title': _('Маркетинг инструменты'),
                'icon': 'fas fa-bullhorn',
                'description': _('Встроенные инструменты для продвижения мероприятий и привлечения аудитории'),
                'features': [
                    _('Email рассылки'),
                    _('Партнерские программы'),
                    _('Промокоды и скидки'),
                    _('SEO оптимизация')
                ]
            },
            {
                'title': _('Управление регистрациями'),
                'icon': 'fas fa-users',
                'description': _('Полный контроль над процессом регистрации и коммуникацией с участниками'),
                'features': [
                    _('Кастомизируемые формы'),
                    _('Автоматические уведомления'),
                    _('Чек-ин система'),
                    _('База данных участников')
                ]
            },
            {
                'title': _('Монетизация'),
                'icon': 'fas fa-money-bill-wave',
                'description': _('Гибкие возможности для заработка на ваших мероприятиях'),
                'features': [
                    _('Многоуровневые цены'),
                    _('Групповые скидки'),
                    _('Регулярные платежи'),
                    _('Краудфандинг')
                ]
            }
        ]
        
        context.update({
            'page_title': _('Решения для организаторов'),
            'solutions': solutions,
            'meta_description': _('Профессиональные инструменты для организаторов мероприятий. Аналитика, маркетинг и управление регистрациями.'),
        })
        return context

class OrganizerResourcesView(TemplateView):
    """Ресурсы для организаторов"""
    template_name = 'events/footer/organizer_resources.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        resources = [
            {
                'category': _('Гайды и инструкции'),
                'items': [
                    {
                        'title': _('Полное руководство по созданию мероприятий'),
                        'type': 'PDF',
                        'size': '2.4 MB',
                        'downloads': '1542'
                    },
                    {
                        'title': _('Шаблоны маркетинговых материалов'),
                        'type': 'ZIP',
                        'size': '8.7 MB',
                        'downloads': '892'
                    },
                    {
                        'title': _('Чек-лист организации мероприятия'),
                        'type': 'DOCX',
                        'size': '0.8 MB',
                        'downloads': '2103'
                    }
                ]
            },
            {
                'category': _('Вебинары и обучение'),
                'items': [
                    {
                        'title': _('Эффективное продвижение мероприятий'),
                        'duration': '45 мин',
                        'instructor': 'Анна Петрова',
                        'views': '3200'
                    },
                    {
                        'title': _('Монетизация онлайн-мероприятий'),
                        'duration': '38 мин',
                        'instructor': 'Максим Иванов',
                        'views': '2850'
                    },
                    {
                        'title': _('Работа с участниками до и после события'),
                        'duration': '52 мин',
                        'instructor': 'Елена Сидорова',
                        'views': '1980'
                    }
                ]
            },
            {
                'category': _('Шаблоны и инструменты'),
                'items': [
                    {
                        'title': _('Шаблон бюджета мероприятия'),
                        'type': 'Excel',
                        'format': 'XLSX',
                        'rating': '4.8'
                    },
                    {
                        'title': _('Планировщик таймлайна'),
                        'type': 'Инструмент',
                        'format': 'Online',
                        'rating': '4.9'
                    },
                    {
                        'title': _('Калькулятор ROI'),
                        'type': 'Калькулятор',
                        'format': 'Online',
                        'rating': '4.7'
                    }
                ]
            }
        ]
        
        success_stories = [
            {
                'title': _('TechConf 2024: 5000+ участников за 2 недели'),
                'organizer': 'Иван Козлов',
                'result': _('+320% к регистрациям с помощью AI-рекомендаций')
            },
            {
                'title': _('Art Festival: 95% заполняемость при 80% онлайн-продаж'),
                'organizer': 'Мария Смирнова',
                'result': _('+150% к доходу с помощью динамического ценообразования')
            },
            {
                'title': _('Startup Pitch: 300 инвесторов из 15 стран'),
                'organizer': 'Алексей Попов',
                'result': _('Международная экспансия через гибридный формат')
            }
        ]
        
        context.update({
            'page_title': _('Ресурсы для организаторов'),
            'resources': resources,
            'success_stories': success_stories,
            'meta_description': _('Бесплатные ресурсы, гайды и инструменты для организаторов мероприятий. Повышайте эффективность ваших событий.'),
        })
        return context

class OrganizerGuidelinesView(TemplateView):
    """Рекомендации для организаторов"""
    template_name = 'events/footer/organizer_guidelines.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        guidelines = [
            {
                'category': _('Создание привлекательного контента'),
                'tips': [
                    _('Используйте качественные фотографии и видео'),
                    _('Пишите подробные и честные описания'),
                    _('Выделяйте уникальные особенности мероприятия'),
                    _('Добавляйте отзывы предыдущих участников')
                ]
            },
            {
                'category': _('Ценообразование и билеты'),
                'tips': [
                    _('Предлагайте несколько ценовых категорий'),
                    _('Используйте early bird скидки'),
                    _('Создавайте групповые тарифы'),
                    _('Предусмотрите бесплатные опции')
                ]
            },
            {
                'category': _('Продвижение мероприятия'),
                'tips': [
                    _('Начните продвижение за 4-6 недель до события'),
                    _('Используйте социальные сети и email рассылки'),
                    _('Сотрудничайте с инфлюенсерами и партнерами'),
                    _('Участвуйте в relevant сообществах')
                ]
            },
            {
                'category': _('Управление мероприятием'),
                'tips': [
                    _('Регулярно общайтесь с зарегистрированными участниками'),
                    _('Подготовьте contingency plan'),
                    _('Собирайте feedback во время и после события'),
                    _('Анализируйте результаты для будущих улучшений')
                ]
            }
        ]
        
        best_practices = [
            {
                'title': _('Оптимальное время для публикации'),
                'description': _('Публикуйте мероприятия за 4-6 недель до даты проведения для максимального охвата'),
                'stat': '+65%'
            },
            {
                'title': _('Эффективность мультимедиа'),
                'description': _('Мероприятия с видео имеют на 80% больше регистраций'),
                'stat': '+80%'
            },
            {
                'title': _('Early bird стратегия'),
                'description': _('Скидки early bird увеличивают общее количество регистраций на 45%'),
                'stat': '+45%'
            }
        ]
        
        context.update({
            'page_title': _('Рекомендации для организаторов'),
            'guidelines': guidelines,
            'best_practices': best_practices,
            'meta_description': _('Проверенные рекомендации и лучшие практики для успешной организации мероприятий на платформе EventHub.'),
        })
        return context
    

# Страницы поддержки
class FAQView(TemplateView):
    template_name = 'events/pages/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faq_categories'] = [
            {
                'title': _('Регистрация и аккаунт'),
                'questions': [
                    {
                        'question': _('Как зарегистрироваться на мероприятие?'),
                        'answer': _('Выберите мероприятие, нажмите "Зарегистрироваться" и следуйте инструкциям. Для платных мероприятий потребуется оплата.')
                    },
                    {
                        'question': _('Как восстановить пароль?'),
                        'answer': _('На странице входа нажмите "Забыли пароль?" и следуйте инструкциям для восстановления.')
                    }
                ]
            },
            {
                'title': _('Оплата и возвраты'),
                'questions': [
                    {
                        'question': _('Какие способы оплаты принимаются?'),
                        'answer': _('Мы принимаем банковские карты, ЮMoney, и другие популярные платежные системы.')
                    }
                ]
            }
        ]
        return context

class ContactView(TemplateView):
    template_name = 'events/pages/contact.html'
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Отправка email
        try:
            send_mail(
                f'Contact Form: {subject}',
                f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}',
                email,
                ['support@eventhub.ru'],
                fail_silently=False,
            )
            messages.success(request, _('Ваше сообщение отправлено! Мы ответим вам в ближайшее время.'))
        except Exception as e:
            messages.error(request, _('Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.'))
        
        return redirect('contact')

class PrivacyPolicyView(TemplateView):
    template_name = 'events/pages/privacy_policy.html'

class TermsOfUseView(TemplateView):
    template_name = 'events/pages/terms_of_use.html'

class RefundPolicyView(TemplateView):
    template_name = 'events/pages/refund_policy.html'

# Страницы для организаторов
class OrganizerSolutionsView(TemplateView):
    template_name = 'events/pages/organizer_solutions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solutions'] = [
            {
                'title': _('Продвижение мероприятий'),
                'description': _('Расширенная видимость в поиске, email-рассылки, таргетированная реклама'),
                'icon': 'fas fa-bullhorn',
                'features': [
                    _('SEO оптимизация мероприятий'),
                    _('Email маркетинг'),
                    _('Таргетированная реклама'),
                    _('Социальные сети интеграция')
                ]
            },
            {
                'title': _('Система продажи билетов'),
                'description': _('Простая интеграция, мгновенные подтверждения, мобильные билеты'),
                'icon': 'fas fa-ticket-alt',
                'features': [
                    _('Онлайн продажа билетов'),
                    _('Мгновенные подтверждения'),
                    _('Мобильные билеты'),
                    _('Система скидок и промокодов')
                ]
            },
            {
                'title': _('Аналитика и отчетность'),
                'description': _('Детальная статистика, отслеживание конверсий, ROI-аналитика'),
                'icon': 'fas fa-chart-bar',
                'features': [
                    _('Детальная аналитика'),
                    _('Отслеживание конверсий'),
                    _('ROI аналитика'),
                    _('Кастомные отчеты')
                ]
            },
            {
                'title': _('Управление участниками'),
                'description': _('Регистрация, проверка, коммуникация и управление участниками'),
                'icon': 'fas fa-users',
                'features': [
                    _('Онлайн регистрация'),
                    _('QR-код проверка'),
                    _('Массовая рассылка'),
                    _('Сегментация участников')
                ]
            },
            {
                'title': _('Мобильное приложение'),
                'description': _('Собственное мобильное приложение для вашего мероприятия'),
                'icon': 'fas fa-mobile-alt',
                'features': [
                    _('Кастомное мобильное приложение'),
                    _('Push уведомления'),
                    _('Интерактивная программа'),
                    _('Карта мероприятия')
                ]
            },
            {
                'title': _('Интеграции и API'),
                'description': _('Интеграция с популярными сервисами и кастомные решения'),
                'icon': 'fas fa-plug',
                'features': [
                    _('REST API'),
                    _('Zapier интеграция'),
                    _('Кастомные интеграции'),
                    _('Webhooks поддержка')
                ]
            }
        ]
        return context

class OrganizerGuidelinesView(TemplateView):
    template_name = 'events/pages/organizer_guidelines.html'

class OrganizerResourcesView(TemplateView):
    template_name = 'events/pages/organizer_resources.html'

class PricingView(TemplateView):
    template_name = 'events/pages/pricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = [
            {
                'name': _('Базовый'),
                'price': '0₽',
                'period': _('бесплатно'),
                'features': [
                    _('До 3 мероприятий одновременно'),
                    _('Базовая аналитика'),
                    _('Email поддержка'),
                    _('Стандартные шаблоны')
                ]
            },
            {
                'name': _('Профессиональный'),
                'price': '2990₽',
                'period': _('/месяц'),
                'features': [
                    _('Неограниченное количество мероприятий'),
                    _('Расширенная аналитика'),
                    _('Приоритетная поддержка'),
                    _('Кастомные шаблоны'),
                    _('Продвижение в поиске')
                ]
            }
        ]
        return context

class SuccessStoriesView(TemplateView):
    template_name = 'events/pages/success_stories.html'

# Страницы компании
class AboutView(TemplateView):
    template_name = 'events/pages/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = [
            {'name': 'Алексей Петров', 'role': _('Основатель & CEO'), 'bio': _('15+ лет в event-индустрии')},
            {'name': 'Мария Иванова', 'role': _('CTO'), 'bio': _('Эксперт в разработке масштабируемых систем')}
        ]
        return context

class BlogView(TemplateView):
    template_name = 'events/pages/blog.html'

class CareersView(TemplateView):
    template_name = 'events/pages/careers.html'

class PressView(TemplateView):
    template_name = 'events/pages/press.html'

class PartnersView(TemplateView):
    template_name = 'events/pages/partners.html'

class APIDocsView(TemplateView):
    template_name = 'events/pages/api_docs.html'

class SitemapView(TemplateView):
    template_name = 'events/pages/sitemap.html'

# Для обратной совместимости
HelpCenterView = FAQView