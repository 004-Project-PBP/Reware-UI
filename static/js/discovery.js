function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

async function post(url, data = {}) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams(data)
    });
    return response.json();
}

document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('item-grid');
    const form = document.getElementById('filter-form');
    const loadMoreBtn = document.getElementById('load-more');

    async function loadCatalog(page = 1, append = false) {
        if (!grid) return;

        const params = new URLSearchParams(new FormData(form));
        params.set('page', page);
        const response = await fetch(`${grid.dataset.api}?${params.toString()}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await response.json();
        if (append) {
            grid.insertAdjacentHTML('beforeend', data.html);
        } else {
            grid.innerHTML = data.html;
        }
        const countEl = document.getElementById('result-count');
        if (countEl) countEl.textContent = data.total;

        if (loadMoreBtn) {
            loadMoreBtn.hidden = !data.has_next;
            loadMoreBtn.dataset.page = data.next_page;
        }
    }

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault(); 
            loadCatalog(1);
        });

        form.addEventListener('change', () => loadCatalog(1));
    }

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', (e) => {
            loadCatalog(parseInt(e.target.dataset.page), true);
        });
    }

    const priceMin = document.querySelector('input[name="price_min"]');
    const priceMax = document.querySelector('input[name="price_max"]');
    const priceLabel = document.getElementById('price-label');
    
    function updatePriceLabel() {
        if (priceLabel && priceMin && priceMax) {
            priceLabel.textContent = `${priceMin.value} – ${priceMax.value}`;
        }
    }
    if (priceMin && priceMax) {
        updatePriceLabel();
        priceMin.addEventListener('input', updatePriceLabel);
        priceMax.addEventListener('input', updatePriceLabel);
    }

    document.addEventListener('click', async (e) => {

        const wishBtn = e.target.closest('.card__wish');
        if (wishBtn) {
            const data = await post(wishBtn.dataset.url, { item_id: wishBtn.dataset.item });
            wishBtn.classList.toggle('is-active', data.added);

            const counter = document.getElementById('wishlist-count');
            if (counter) counter.textContent = data.count;
            return;
        }

        const contactBtn = e.target.closest('.card__contact');
        if (contactBtn) {
            const response = await fetch(contactBtn.dataset.url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await response.json();
            if (data.name) {
                contactBtn.textContent = `${data.name} (${data.email})`;
                contactBtn.disabled = true;
            } else {
                alert("Silakan login untuk melihat kontak seller.");
            }
            return;
        }

        const deleteBtn = e.target.closest('[data-delete-url], [data-wish-delete]');
        if (deleteBtn) {
            const url = deleteBtn.dataset.deleteUrl || deleteBtn.dataset.wishDelete;
            const payload = {};
            if (deleteBtn.dataset.item) payload.item_id = deleteBtn.dataset.item;
            
            await post(url, payload);
            
            // Remove the row from DOM
            const row = deleteBtn.closest('.wish__row, .page__row');
            if (row) row.remove();

            // Show empty state if wishlist is now empty
            const emptyState = document.getElementById('w-empty');
            if (emptyState && document.querySelectorAll('.wish__row').length === 0) {
                emptyState.hidden = false;
            }
            return;
        }

        const noteBtn = e.target.closest('[data-note-url]');
        if (noteBtn) {
            const row = noteBtn.closest('.wish__row');
            const currentNote = row.querySelector('.wish__note-text').textContent;
            const newNote = prompt("Ubah catatan pribadi:", currentNote);
            
            if (newNote !== null) {
                await post(noteBtn.dataset.noteUrl, { note: newNote });
                row.querySelector('.wish__note-text').textContent = newNote;
            }
            return;
        }
    });

    const saveSearchBtn = document.getElementById('save-search');
    if (saveSearchBtn) {
        saveSearchBtn.addEventListener('click', async () => {
            const label = prompt("Beri nama pencarian ini:");
            if (!label) return;

            const params = Object.fromEntries(new FormData(form));
            delete params.page; // Don't save pagination state

            await post(saveSearchBtn.dataset.url, {
                label: label,
                q: params.q || '',
                filters: JSON.stringify(params)
            });
            alert("Pencarian berhasil disimpan!");
        });
    }
});