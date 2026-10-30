
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    if (!form) return;

    const minInput = form.querySelector('[name="retail_price_min"]');
    const maxInput = form.querySelector('[name="retail_price_max"]');

    if (minInput && maxInput) {
        form.addEventListener('submit', (event) => {
            const minVal = parseFloat(minInput.value) || 0;
            const maxVal = parseFloat(maxInput.value) || 0;

            if (maxVal > 0 && minVal > maxVal) {
                event.preventDefault();
                alert('Harga ritel minimum tidak boleh lebih besar dari harga ritel maksimum.');
                minInput.focus();
            }
        });
    }
});