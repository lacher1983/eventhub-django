document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/api/events/calendar/',
        eventClick: function(info) {
            window.location.href = `/event/${info.event.id}/`;
        },
        eventContent: function(info) {
            return {
                html: `
                    <div class="fc-event-content p-1">
                        <div class="fw-bold">${info.event.title}</div>
                        <small>${info.event.extendedProps.location}</small>
                    </div>
                `
            };
        }
    });
    calendar.render();
});