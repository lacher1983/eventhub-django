class EventService:
    @staticmethod
    def get_events_with_stats():
        return Event.objects.annotate(
            registrations_count=Count('registrations'),
            avg_rating=Avg('reviews__rating')
        )