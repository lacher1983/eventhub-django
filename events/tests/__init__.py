class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Технологии',
            slug='technology'
        )
    
    def test_event_creation(self):
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=timezone.now() + timedelta(days=7),
            location='Test Location',
            event_type='online',
            category=self.category,
            organizer=self.user,
            price=1000
        )
        self.assertEqual(event.title, 'Test Event')
        self.assertTrue(event.is_active)