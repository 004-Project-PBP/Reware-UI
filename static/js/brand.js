// read Django's CSRF cookie for POST requests
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Follow or Unfollow Brand button with live counter
document.addEventListener("click", async (event) => {
  const followBtn = event.target.closest(".js-follow-btn");
  if (!followBtn) return;

  event.preventDefault();
  const url = followBtn.dataset.url;
  const labelEl = followBtn.querySelector(".js-follow-label");
  const countEl = followBtn.querySelector(".js-follower-count");

  followBtn.disabled = true;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    });

    if (response.ok) {
      const data = await response.json();
      // Example expected JSON: { "status": "success", "is_following": true/false, "follower_count": 12 }
      followBtn.classList.toggle("is-following", data.is_following);
      if (labelEl) {
        labelEl.textContent = data.is_following ? "Mengikuti" : "+ Ikuti";
      }
      if (countEl) {
        countEl.textContent = data.follower_count;
      }
    }
  } catch (error) {
    console.error("Gagal memperbarui status follow:", error);
  } finally {
    followBtn.disabled = false;
  }
});

// Brand Directory filter menu
const filterForm = document.getElementById("brand-filter-form");
const brandGrid = document.getElementById("brand-grid");

if (filterForm && brandGrid) {
  let debounceTimer;

  const fetchFilteredBrands = async () => {
    const params = new URLSearchParams(new FormData(filterForm));
    const url = `${window.location.pathname}?${params.toString()}`;

    try {
      const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (response.ok) {
        const htmlText = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, "text/html");
        const newGrid = doc.getElementById("brand-grid");

        if (newGrid) {
          brandGrid.innerHTML = newGrid.innerHTML;
          // Make new cards visible immediately
          brandGrid
            .querySelectorAll(".reveal")
            .forEach((el) => el.classList.add("is-visible"));
        }
      }
    } catch (error) {
      console.error("Gagal memfilter direktori brand:", error);
    }
  };

  // Interactivity modifiers
  filterForm.addEventListener("change", fetchFilteredBrands);
  filterForm.addEventListener("input", (event) => {
    if (event.target.tagName === "INPUT") {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchFilteredBrands, 250);
    }
  });
}
