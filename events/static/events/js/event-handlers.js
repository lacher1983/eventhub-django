document.addEventListener('DOMContentLoaded', function() {
    // AJAX добавление в корзину
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const eventId = this.dataset.eventId;
            
            fetch(`/cart/add/${eventId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                updateCartCounter(data.items_count);
                showNotification('Товар добавлен в корзину!');
            });
        });
    });
});