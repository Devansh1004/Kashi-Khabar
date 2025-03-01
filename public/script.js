window.onload = function () {
    // Check for dark mode preference in localStorage
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('night-mode');
    }

    document.getElementById("searchButton").addEventListener("click", searchArticles);
    document.getElementById("searchBar").addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            searchArticles();
        }
    });
    document.getElementById("nightModeButton").addEventListener("click", toggleDarkMode);

    // Initial fetch to display all articles
    fetchArticles();
};

async function searchArticles() {
    let query = document.getElementById("searchBar").value.trim();
	
    const selectedGenres = getSelectedGenres();
    console.log(selectedGenres);

    if (query.length === 0 && selectedGenres.length === 0) {
        fetchArticles(); // Fetch all articles if no query and no selected genres
    } else {
        fetch(`/api/search?q=${encodeURIComponent(query)}&genres=${encodeURIComponent(selectedGenres.join(','))}`)
            .then(response => response.json())
            .then(data => displayArticles(data))
            .catch(error => console.error("Error fetching search results:", error));
    }
}

function filterArticlesByGenre() {
    const selectedGenres = getSelectedGenres();

    if (selectedGenres.length > 0) {
        // Fetch articles based on selected genres
        fetch(`/api/get_articles`)
            .then(response => response.json())
            .then(data => {
                const filteredArticles = data.filter(article =>
                    selectedGenres.some(genre => article.keywords.includes(genre)) // Assuming 'keywords' is an array in your MongoDB schema
                );
                displayArticles(filteredArticles);
            })
            .catch(error => console.error("Error fetching articles:", error));
    } else {
        fetchArticles(); // If no genres are selected, fetch all articles
    }
}

function getSelectedGenres() {
    const checkboxes = document.querySelectorAll("#sidebar input[type='checkbox']");
    const selectedGenres = [];
    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            selectedGenres.push(checkbox.value);
        }
    });
    return selectedGenres;
}

function fetchArticles() {
    fetch(`/api/get_articles`)
        .then(response => response.json())
        .then(data => displayArticles(data))
        .catch(error => console.error("Error fetching articles:", error));
}

function displayArticles(articles) {
    const resultsContainer = document.getElementById("articles-container");
    resultsContainer.innerHTML = "";

    if (articles.length === 0) {
        resultsContainer.innerHTML = "No articles found.";
        return;
    }

    articles.forEach(article => {
        const capsule = document.createElement("div");
        capsule.classList.add("capsule");
        capsule.style.cursor = 'pointer';

        const img = document.createElement("img");
        img.src = article.image; // Assuming the API returns an image URL
        img.alt = article.title;

        const title = document.createElement("h3");
        title.innerText = article.title;

        capsule.appendChild(img);
        capsule.appendChild(title);

        // Link to the corresponding blog page
        capsule.onclick = () => {
            window.location.href = article.link; // Link from the API response
        };

        resultsContainer.appendChild(capsule);
    });
}

function toggleDarkMode() {
    const isDarkMode = document.body.classList.toggle('night-mode');
    // Save the user's preference to localStorage
    localStorage.setItem('darkMode', isDarkMode);
}

// Update filterArticles function to listen for changes in checkboxes
document.querySelectorAll("#sidebar input[type='checkbox']").forEach(checkbox => {
    checkbox.addEventListener('change', filterArticlesByGenre);
});
