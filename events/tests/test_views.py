class EventListViewTest(TestCase):
    def test_event_list_view(self):
        response = self.client.get(reverse('events:event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Мероприятия")