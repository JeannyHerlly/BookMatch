/*
  BookMatch frontend

  API contract expected by this file:

  GET /api/search?q=kokoro
    -> [
      {
        id: 4786,
        title: "Kokoro",
        authors: "Natsume Sôseki",
        categories: "Fiction",
        published_date: "1996-07-01",
        thumbnail: "https://..."
      }
    ]

  POST /api/recommend
    body:
    {
      "title": "Kokoro",
      "author": "Natsume Sôseki",
      "n": 10
    }

    -> {
      "book": { ... },
      "recommendations": [
        {
          "id": 123,
          "title": "...",
          "authors": "...",
          "categories": "...",
          "thumbnail": "...",
          "similarity": 0.72,
          "author_bonus": 0.15,
          "final_score": 0.87
        }
      ]
    }

  If your Flask/FastAPI routes use different names, only change API_CONFIG.
*/

const API_CONFIG = {
  search: "/api/search",
  recommend: "/api/recommend",
  discover: "/api/discover",
  useDemoData: false
};

/* Demo data lets you build/test the UI before connecting Python. */
const demoBooks = [
  {
    id: 1,
    title: "Flashlight",
    authors: "Susan Choi",
    categories: "Fiction",
    published_date: "2007",
    description: "A literary novel about family, mystery, memory, and a life changed by a strange nighttime event.",
    thumbnail: ""
  },
  {
    id: 2,
    title: "The Night Ocean",
    authors: "Paul La Farge",
    categories: "Fiction",
    published_date: "2010",
    description: "A literary mystery blending strange discoveries, writers, secrets, and speculative ideas.",
    thumbnail: ""
  },
  {
    id: 3,
    title: "PARADOX",
    authors: "Margarita Perez",
    categories: "Sci-fi",
    published_date: "2016",
    description: "A speculative story exploring identity, uncertainty, and the boundaries between realities.",
    thumbnail: ""
  },
  {
    id: 4,
    title: "Educated",
    authors: "Tara Westover",
    categories: "Autobiography",
    published_date: "2022",
    description: "A memoir about education, family, identity, and discovering a different way of understanding the world.",
    thumbnail: ""
  },
  {
    id: 5,
    title: "Wicked",
    authors: "Gregory Maguire",
    categories: "Fantasy",
    published_date: "1995",
    description: "A reimagining of Oz that explores friendship, politics, identity, and the stories behind familiar characters.",
    thumbnail: ""
  },
  {
    id: 6,
    title: "Sleeping Murder",
    authors: "Agatha Christie",
    categories: "Mystery",
    published_date: "1989",
    description: "A mystery involving an old house, buried memories, and a long-hidden secret.",
    thumbnail: ""
  },
  {
    id: 7,
    title: "Kokoro",
    authors: "Natsume Sôseki",
    categories: "Fiction",
    published_date: "1914",
    description: "A psychological novel exploring friendship, guilt, isolation, and the changing social world of Japan.",
    thumbnail: ""
  },
  {
    id: 8,
    title: "Kokoro",
    authors: "Lafcadio Hearn",
    categories: "Literary Collections",
    published_date: "1896",
    description: "A collection of essays about Japanese culture, customs, beliefs, and everyday life.",
    thumbnail: ""
  },
  {
    id: 9,
    title: "The Trial",
    authors: "Franz Kafka",
    categories: "Fiction",
    published_date: "1925",
    description: "A surreal and unsettling novel about an individual caught inside an opaque legal system.",
    thumbnail: ""
  },
  {
    id: 10,
    title: "The Metamorphosis",
    authors: "Franz Kafka",
    categories: "Fiction",
    published_date: "1915",
    description: "A famous literary work about alienation, family relationships, identity, and transformation.",
    thumbnail: ""
  }
];

const state = {
  currentCategory: "All",
  currentBook: null,
  searchTimer: null
};

const $ = (selector) => document.querySelector(selector);

const homeView = $("#homeView");
const searchView = $("#searchView");
const detailView = $("#detailView");
const searchInput = $("#searchInput");
const clearSearch = $("#clearSearch");
const searchDropdown = $("#searchDropdown");
const homeGrid = $("#homeGrid");
const searchResults = $("#searchResults");
const recommendationGrid = $("#recommendationGrid");
const selectedBook = $("#selectedBook");
const searchSummary = $("#searchSummary");

function escapeHTML(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function firstAuthor(authors = "") {
  return String(authors)
    .split(",")
    .map(x => x.trim())
    .filter(Boolean)[0] || "Unknown author";
}

function firstCategory(categories = "") {
  return String(categories)
    .split(",")
    .map(x => x.trim())
    .filter(Boolean)[0] || "Uncategorized";
}

function coverHTML(book, className = "book-cover") {
  const title = book.title || "";
  const colors = [
    "cover-blue",
    "cover-green",
    "cover-purple",
    "cover-teal",
    "cover-orange",
    "cover-mustard",
    "cover-terracotta",
    "cover-black",
    "cover-indigo"
  ];

  const accentColors = {
    "cover-blue": [
      "#F4A260"
    ],

    "cover-green": [
      "#B87333"
    ],

    "cover-purple": [
      "#E7D860"
    ],

    "cover-teal": [
      "#F4A261"
    ],

    "cover-orange": [
      "#FFF9F6"
    ],

    "cover-mustard": [
      "#1A1A17"
    ],

    "cover-terracotta": [
      "#F5C880"
    ],

    "cover-black": [
      "#E63946"
    ],

    "cover-indigo": [
      "#00E895"
    ]
  };


  let hash = 0;

  for (let i = 0; i < title.length; i++) {
    hash = title.charCodeAt(i) + ((hash << 5) - hash);
  }

  const colorIndex = Math.abs(hash) % colors.length;
  const colorClass = colors[colorIndex];

  const possibleAccents = accentColors[colorClass] || [];

  const accent =
    possibleAccents.length > 0
      ? possibleAccents[Math.abs(hash >> 3) % possibleAccents.length]
      : "";

  return `
    <span
      class="${className} cover-fallback ${colorClass}"
      style="--cover-accent: ${accent};"
    >
      <span class="cover-title">
        ${escapeHTML(book.title || "")}
      </span>

      <span class="cover-author">
        ${escapeHTML(firstAuthor(book.authors))}
      </span>
    </span>
  `;
}

function scoreToPercent(score) {
  if (score === undefined || score === null || Number.isNaN(Number(score))) return null;
  const value = Number(score);
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}% match`;
}

function bookCard(book, showScore = false) {
  const score = scoreToPercent(book.final_score ?? book.similarity);

  return `
    <article class="book-card">
      <button
        class="book-card-button"
        type="button"
        data-book-id="${escapeHTML(book.google_id ?? book.id ?? "")}"
      >
        ${coverHTML(book)}

        <span class="book-info">
          <span class="book-title">
            ${escapeHTML(book.title || "Untitled")}
          </span>

          <span class="book-author">
            ${escapeHTML(firstAuthor(book.authors) || "Unknown author")}
          </span>

          <span class="book-category">
            ${escapeHTML(firstCategory(book.categories) || "Uncategorized")}
          </span>

          ${showScore && score
            ? `<span class="match-badge">${score}</span>`
            : ""}
        </span>
      </button>
    </article>
  `;
}

function showView(view) {
  [homeView, searchView, detailView].forEach(v => v.classList.add("hidden"));
  view.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

function getDemoBooksByQuery(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  return demoBooks.filter(book => {
    const haystack = [
      book.title,
      book.authors,
      book.categories,
      book.description
    ].join(" ").toLowerCase();

    return haystack.includes(q);
  }).slice(0, 7);
}

async function searchBooks(query) {
  if (API_CONFIG.useDemoData) {
    return getDemoBooksByQuery(query);
  }

  const response = await fetch(`${API_CONFIG.search}?q=${encodeURIComponent(query)}`);
  if (!response.ok) throw new Error("Search request failed.");
  return response.json();
}

async function getDiscoverBooks(count = 5, category = "All") {
  const url =
    `${API_CONFIG.discover}?count=${count}&category=${encodeURIComponent(category)}`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error("Discover request failed.");
  }

  return response.json();
}

async function getRecommendations(book) {
  if (API_CONFIG.useDemoData) {
    const sameCategory = demoBooks.filter(b =>
      b.id !== book.id &&
      firstCategory(b.categories).toLowerCase() === firstCategory(book.categories).toLowerCase()
    );

    const rest = demoBooks.filter(b => b.id !== book.id && !sameCategory.includes(b));

    return [...sameCategory, ...rest].slice(0, 10).map((b, i) => ({
      ...b,
      similarity: Math.max(.55, .86 - i * .035),
      final_score: Math.max(.55, .86 - i * .035)
    }));
  }

  const response = await fetch(API_CONFIG.recommend, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: book.title,
      author: firstAuthor(book.authors),
      n: 10
    })
  });

  if (!response.ok) throw new Error("Recommendation request failed.");

  const data = await response.json();

  // Accept either {recommendations: [...]} or just [...]
  return Array.isArray(data) ? data : (data.recommendations || []);
}

async function renderHome() {
  const category = state.currentCategory;

  homeGrid.innerHTML = `
    <div class="loading">
      Loading books...
    </div>
  `;

  try {
    const books = await getDiscoverBooks(20, category);

    window.__discoverBooks = books;

    const visibleBooks = books.slice(0, 5);

    if (visibleBooks.length === 0) {
      homeGrid.innerHTML = `
        <div class="empty-state">
          No books found in this category.
        </div>
      `;
      return;
    }

    homeGrid.innerHTML = visibleBooks
      .map(book => bookCard(book))
      .join("");

  } catch (error) {
    console.error("Discover error:", error);

    homeGrid.innerHTML = `
      <div class="empty-state">
        Could not load books.
      </div>
    `;
  }
}

function renderSearchDropdown(results) {
  if (!results.length) {
    searchDropdown.innerHTML = `
      <div class="empty-state">No books found.</div>
    `;

    searchDropdown.classList.remove("hidden");
    return;
  }

  searchDropdown.innerHTML = results.map(book => `
    <button
      class="search-result"
      type="button"
      data-book-id="${escapeHTML(book.google_id ?? book.id)}"
    >
      ${coverHTML(book, "result-cover")}

      <span class="search-result-info">
        <span class="result-title">
          ${escapeHTML(book.title)}
        </span>

        <span class="result-meta">
          ${escapeHTML(firstAuthor(book.authors))}
          ·
          ${escapeHTML(firstCategory(book.categories))}
        </span>
      </span>

      <span class="result-year">
        ${escapeHTML(book.published_date || "")}
      </span>
    </button>
  `).join("");

  searchDropdown.classList.remove("hidden");
}

function renderSearchPage(results, query) {
  searchSummary.textContent =
    `${results.length} result${results.length === 1 ? "" : "s"} for “${query}”`;

  searchResults.innerHTML = results.length
    ? results.map((book, index) => `
        <button
          class="search-result-large"
          type="button"
          data-search-index="${index}"
        >
          ${coverHTML(book, "result-cover")}

          <span class="search-result-info">
            <span class="result-large-title">
              ${escapeHTML(book.title)}
            </span>

            <span class="result-meta">
              ${escapeHTML(firstAuthor(book.authors))}
              ·
              ${escapeHTML(firstCategory(book.categories))}
            </span>
          </span>

          <span class="select-book">Select</span>
        </button>
      `).join("")
    : `
        <div class="empty-state">
          No books matched your search.
        </div>
      `;

  showView(searchView);

  searchResults
    .querySelectorAll(".search-result-large")
    .forEach(button => {
      button.addEventListener("click", () => {
        const index = Number(button.dataset.searchIndex);
        const book = results[index];

        if (book) {
          openBook(book);
        }
      });
    });
}


async function openBook(book) {
  console.log("OPEN BOOK FIRED:", book);
  if (!book) return;

  state.currentBook = book;

  searchDropdown.classList.add("hidden");

  selectedBook.innerHTML = `
    ${coverHTML(book, "selected-cover")}

    <div class="selected-content">
      <h1>${escapeHTML(book.title || "")}</h1>

      <p class="selected-author">
        By ${escapeHTML(firstAuthor(book.authors))}
      </p>

      <p class="selected-description">
        ${escapeHTML(book.description || "No description available.")}
      </p>

      <p class="selected-category">
        ${escapeHTML(firstCategory(book.categories))}
      </p>
    </div>
  `;

recommendationGrid.innerHTML = recommendations.length
  ? recommendations.map((book, index) => `
      <article class="book-card">
        <button
          class="book-card-button recommendation-button"
          type="button"
          data-recommendation-index="${index}"
        >
          ${coverHTML(book)}

          <span class="book-info">
            <span class="book-title">
              ${escapeHTML(book.title || "")}
            </span>

            <span class="book-author">
              ${escapeHTML(firstAuthor(book.authors))}
            </span>

            <span class="book-category">
              ${escapeHTML(firstCategory(book.categories))}
            </span>
          </span>
        </button>
      </article>
    `).join("")
  : `
      <div class="empty-state">
        No recommendations found.
      </div>
    `;

  showView(detailView);

  try {
    const recommendations = await getRecommendations(book);
    window.__recommendationBooks = recommendations;
    console.log("Selected book:", book);
    console.log("Recommendations:", recommendations);

    console.log("Recommendations received:", recommendations);

if (!recommendations.length) {
  recommendationGrid.innerHTML = `
    <div class="empty-state">
      No recommendations found.
    </div>
  `;
} else {
  recommendationGrid.innerHTML = recommendations
    .map((book, index) => `
      <article class="book-card">
        <button
          class="book-card-button recommendation-button"
          type="button"
          data-recommendation-index="${index}"
        >
          ${coverHTML(book)}

          <span class="book-info">
            <span class="book-title">
              ${escapeHTML(book.title || "")}
            </span>

            <span class="book-author">
              ${escapeHTML(firstAuthor(book.authors))}
            </span>

            <span class="book-category">
              ${escapeHTML(firstCategory(book.categories))}
            </span>
          </span>

          <span class="match-badge">
            ${scoreToPercent(book.final_score ?? book.similarity)}
          </span>
        </button>
      </article>
    `)
    .join("");

  recommendationGrid
    .querySelectorAll(".recommendation-button")
    .forEach((button, index) => {
      button.addEventListener("click", () => {
        const selectedRecommendation = recommendations[index];

        console.log(
          "RECOMMENDED BOOK CLICKED:",
          selectedRecommendation
        );

        openBook(selectedRecommendation);
      });
    });
}

  } catch (error) {
    console.error("Recommendation error:", error);

    recommendationGrid.innerHTML = `
      <div class="empty-state">
        Could not load recommendations.
      </div>
    `;
  }
}

function findBookById(id) {
  const allBooks = [
    ...(window.__lastSearchResults || []),
    ...(window.__discoverBooks || []),
    ...(window.__recommendationBooks || [])
  ];

  return allBooks.find(book => {
    const bookId = book.google_id ?? book.id;
    return String(bookId) === String(id);
  });
}

async function openBook(book) {
  if (!book) return;

  state.currentBook = book;
  searchDropdown.classList.add("hidden");

  selectedBook.innerHTML = `
    ${coverHTML(book, "selected-cover")}

    <div class="selected-content">
      <h1>${escapeHTML(book.title || "")}</h1>

      <p class="selected-author">
        By ${escapeHTML(firstAuthor(book.authors))}
      </p>

      <p class="selected-description">
        ${escapeHTML(book.description || "No description available.")}
      </p>

      <p class="selected-category">
        ${escapeHTML(firstCategory(book.categories))}
      </p>
    </div>
  `;

  recommendationGrid.innerHTML = `
    <div class="loading">
      Finding books for you...
    </div>
  `;

  showView(detailView);

  try {
    const recommendations = await getRecommendations(book);

    if (!recommendations.length) {
      recommendationGrid.innerHTML = `
        <div class="empty-state">
          No recommendations found.
        </div>
      `;
      return;
    }

    recommendationGrid.innerHTML = recommendations
      .map((recommendedBook, index) => `
        <article class="book-card">
          <button
            class="book-card-button recommendation-button"
            type="button"
            data-recommendation-index="${index}"
          >
            ${coverHTML(recommendedBook)}

            <span class="book-info">
              <span class="book-title">
                ${escapeHTML(recommendedBook.title || "")}
              </span>

              <span class="book-author">
                ${escapeHTML(firstAuthor(recommendedBook.authors))}
              </span>

              <span class="book-category">
                ${escapeHTML(firstCategory(recommendedBook.categories))}
              </span>
            </span>

            <span class="match-badge">
              ${scoreToPercent(
                recommendedBook.final_score ??
                recommendedBook.similarity
              )}
            </span>
          </button>
        </article>
      `)
      .join("");

    recommendationGrid
      .querySelectorAll(".recommendation-button")
      .forEach((button, index) => {
        button.addEventListener("click", () => {
          console.log(
            "RECOMMENDATION CLICK:",
            recommendations[index]
          );

          openBook(recommendations[index]);
        });
      });

  } catch (error) {
    console.error("Recommendation error:", error);

    recommendationGrid.innerHTML = `
      <div class="empty-state">
        The recommendation service could not be reached.
      </div>
    `;
  }
}

function handleBookClick(id) {
  const book = findBookById(id);

  if (!book) {
    console.warn("Book not found:", id);
    return;
  }

  openBook(book);
}

async function performSearch(query, openFullPage = false) {
  const trimmed = query.trim();

  if (!trimmed) {
    searchDropdown.classList.add("hidden");
    return;
  }

  try {
    const results = await searchBooks(trimmed);
    window.__lastSearchResults = results;

    if (openFullPage) {
      renderSearchPage(results, trimmed);
    } else {
      renderSearchDropdown(results);
    }
  } catch (error) {
    console.error(error);
    searchDropdown.innerHTML = `<div class="empty-state">Search service unavailable.</div>`;
    searchDropdown.classList.remove("hidden");
  }
}

searchInput.addEventListener("input", () => {
  clearSearch.style.display = searchInput.value ? "block" : "none";

  clearTimeout(state.searchTimer);

  if (!searchInput.value.trim()) {
    searchDropdown.classList.add("hidden");
    return;
  }

  state.searchTimer = setTimeout(() => {
    performSearch(searchInput.value);
  }, 180);
});

searchInput.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    event.preventDefault();
    performSearch(searchInput.value, true);
  }

  if (event.key === "Escape") {
    searchDropdown.classList.add("hidden");
  }
});

clearSearch.addEventListener("click", () => {
  searchInput.value = "";
  clearSearch.style.display = "none";
  searchDropdown.classList.add("hidden");
  searchInput.focus();
});

document.addEventListener("click", event => {
  if (event.target.closest(".recommendation-button")) {
    return;
  }

  const bookButton = event.target.closest("[data-book-id]");

  if (bookButton) {
    handleBookClick(bookButton.dataset.bookId);
    return;
  }

  if (!event.target.closest(".search-shell")) {
    searchDropdown.classList.add("hidden");
  }
});


$("#categoryFilters").addEventListener("click", event => {
  const button = event.target.closest(".category");
  if (!button) return;

  document.querySelectorAll(".category").forEach(b => b.classList.remove("active"));
  button.classList.add("active");

  state.currentCategory = button.dataset.category;
  
  renderHome();
});

$("#backHome").addEventListener("click", () => {
  showView(homeView);
});

$("#backHomeFromSearch").addEventListener("click", () => {
  showView(homeView);
});

renderHome();
