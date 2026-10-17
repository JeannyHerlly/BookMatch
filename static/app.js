const state = {
  currentCategory: "All",
  currentBook: null,
  detailHistory: [],
  detailReturnView: null,
  searchTimer: null
};

const $ = (selector) => document.querySelector(selector);

const homeView = $("#homeView");
const searchView = $("#searchView");
const detailView = $("#detailView");
const likedView = document.getElementById("likedView");
const likedGrid = document.getElementById("likedGrid");
const likedButton = document.getElementById("openLikedBooks");
const openLikedBooksButton = document.getElementById("openLikedBooks");
const backFromLikedButton = document.getElementById("backFromLiked");
const likedCount = document.getElementById("likedCount");
const searchInput = $("#searchInput");
const clearSearch = $("#clearSearch");
const searchDropdown = $("#searchDropdown");
const homeGrid = $("#homeGrid");
const searchResults = $("#searchResults");
const recommendationGrid = $("#recommendationGrid");
const selectedBook = $("#selectedBook");
const searchSummary = $("#searchSummary");
const API_CONFIG = {discover: "/api/discover", search: "/api/search", recommend: "/api/recommend"};

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


function updatePersonalizedSection() {
    const heading = document.getElementById("personalizedHeading");
    const emptyMessage = document.getElementById("personalizedEmptyMessage");
    const grid = document.getElementById("personalizedGrid");

    const hasLikedBooks = likedBookIds.size > 0;

    heading.hidden = !hasLikedBooks;
    emptyMessage.hidden = hasLikedBooks;

    if (!hasLikedBooks) {
        grid.innerHTML = "";
    }
}


function firstCategory(categories = "") {
  return String(categories)
    .split(",")
    .map(x => x.trim())
    .filter(Boolean)[0] || "Uncategorized";
}


function coverHTML(book, className = "book-cover", badgeHTML = "") {
  const title = book.title || "";

  const colors = [
    "cover-blue",
    "cover-dark-blue",
    "cover-muted-blue",
    "cover-leaf-green",
    "cover-green-light",
    "cover-purple-light",
    "cover-lilac",
    "cover-pink",
    "cover-salmon",
    "cover-peach",
    "cover-teal"
  ];

  const accentColors = {
    "cover-blue": ["#d2ebf7","#425c83","#bfe4eb"],
    "cover-muted-blue": ["#cee4f0"],
    "cover-dark-blue": ["#c9cde9"],
    "cover-leaf-green": ["#a3c2ad"],
    "cover-green-light": ["#C4DFD1","#c1e7ec"],
    "cover-purple-light": ["#E0C3FC","#f2d8d2"],
    "cover-pink": ["#ffefed","#493041"],
    "cover-peach": ["#ffe4e2"],
    "cover-teal": ["#cadcf6","#a1e5d9"],
    "cover-lilac": ["#eecfff","#321242"],
    "cover-salmon": ["#7c413c"],
    "cover-indigo": ["#4FC3F7"]
  };

  let hash = 0;

  for (let i = 0; i < title.length; i++) {
    hash = title.charCodeAt(i) + ((hash << 2) - hash);
  }

  const colorClass = colors[Math.abs(hash) % colors.length];
  const possibleAccents = accentColors[colorClass] || [];
  const accent = possibleAccents.length
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
        ${escapeHTML(firstAuthor(book.authors) || "")}
      </span>

      ${badgeHTML}
    </span>
  `;
}


function scoreToPercent(score) {
  if (score === undefined || score === null || Number.isNaN(Number(score))) return null;
  const value = Number(score);
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}% match`;
}



const likedBookIds = new Set();


function likeButtonHTML(book) {
  const googleId = String(book.google_id || "").trim();
  const isLiked = likedBookIds.has(googleId);

  return `
    <button
      type="button"
      class="like-button ${isLiked ? "is-liked" : ""}"
      data-google-id="${googleId}"
      aria-pressed="${isLiked}"
      aria-label="${isLiked ? "Unlike" : "Like"} this book"
      title="${isLiked ? "Remove from liked books" : "Add to liked books"}"
    >
      ${isLiked ? "♥" : "♡"}
    </button>
  `;
}

async function loadCategories() {
    const response = await fetch("/api/categories");
    const categories = await response.json();

    const select = document.getElementById("category-filter");

    categories.forEach(category => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        select.appendChild(option);
    });
}

async function loadLikedBooks() {
  try {
    const response = await fetch("/api/likes");
    if (!response.ok) throw new Error("Could not load liked books.");

    const data = await response.json();
    const books = Array.isArray(data) ? data : (data.likes || []);

    likedBookIds.clear();

  books.forEach(book => {
    if (book.google_id != null && String(book.google_id).trim()) {
      likedBookIds.add(String(book.google_id));
    }
  });

    updateLikedCount();
    updatePersonalizedSection();

    // Update the visible saved-books page, if present.
    await renderLikedBooks();


  } catch (error) {
    console.error("Could not load saved likes:", error);
  }
}


function updateVisibleLikeButtons(googleId, isLiked) {
  document.querySelectorAll(".like-button").forEach(button => {
    if (button.dataset.googleId !== String(googleId)) return;

    button.classList.toggle("is-liked", isLiked);
    button.setAttribute("aria-pressed", String(isLiked));
    button.setAttribute(
      "aria-label",
      `${isLiked ? "Unlike" : "Like"} this book`
    );
  });
}



function updateLikedCount() {
  const countElement = document.getElementById("likedCount");

  if (countElement) {
    countElement.textContent = likedBookIds.size;
  }
}

function getBestsellerBadge(book) {
    const value = book.is_bestseller;

    const isBestseller =
        value === true ||
        value === 1 ||
        ["true", "1", "yes"].includes(
            String(value).toLowerCase()
        );

    if (!isBestseller) return "";

    return `<span class="bestseller-badge">BESTSELLER</span>`;
}



function bookCard(book, showScore = false) {
  const score = scoreToPercent(
    book.final_score ?? book.similarity
  );

  const isAwardWinner =
    book.is_award_winner === true ||
    book.is_award_winner === 1 ||
    (
      typeof book.is_award_winner === "string" &&
      ["true", "1"].includes(
        book.is_award_winner.trim().toLowerCase()
      )
    );

  const awardNames = Array.isArray(book.award_names)
    ? book.award_names
    : book.award_names
      ? [book.award_names]
      : [];

  const awardLabel =
    isAwardWinner && awardNames.length
      ? `
        <span class="award-name">
          🏆 ${escapeHTML(awardNames.join(", "))}
        </span>
      `
      : "";


const cover = coverHTML(
    book,
    "book-cover",
    `${getAwardBadge(book)}${getBestsellerBadge(book)}`
);


return `
  <article class="book-card">
    ${likeButtonHTML(book)}

    <button
      class="book-card-button"
      type="button"
      data-book-id="${escapeHTML(book.google_id ?? book.id ?? "")}"
    >
      ${cover}

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
`;}



if (likedGrid) {
  likedGrid.addEventListener("click", (event) => {
    // Let the heart button handle its own click.
    if (
      event.target.closest(".like-button") ||
      event.target.closest(".google-books-link")
    ) {
      return;
    }

    const card = event.target.closest(".book-card-button");
    if (!card) return;

    const googleId = String(card.dataset.bookId || "").trim();

    const book = (window.__likedBooks || []).find(
      item => String(item.google_id || item.id || "").trim() === googleId
    );

    if (book) {
      openBook(book);
    } else {
      console.warn("Liked book not found:", googleId);
    }
  });
}



document.addEventListener("click", async (event) => {
  const button = event.target.closest(".like-button");
  if (!button) return;

  event.preventDefault();
  event.stopPropagation();

  const googleId = String(button.dataset.googleId || "").trim();
  if (!googleId || button.disabled) return;

  const wasLiked = likedBookIds.has(googleId);
  button.disabled = true;

  try {
    const response = await fetch(
      wasLiked
        ? `/api/likes/${encodeURIComponent(googleId)}`
        : "/api/likes",
      {
        method: wasLiked ? "DELETE" : "POST",
        headers: { "Content-Type": "application/json" },
        ...(!wasLiked
          ? { body: JSON.stringify({ google_id: googleId }) }
          : {})
      }
    );

    if (!response.ok) {
      throw new Error(`Like request failed: ${response.status}`);
    }

    // Update the saved IDs.
    if (wasLiked) {
      likedBookIds.delete(googleId);
    } else {
      likedBookIds.add(googleId);
    }

    updateLikedCount();
    updatePersonalizedSection();

    // Update every visible copy without rebuilding the page.
    document.querySelectorAll(".like-button").forEach((heart) => {
      if (String(heart.dataset.googleId || "") !== googleId) return;

      heart.classList.toggle("is-liked", !wasLiked);
      heart.setAttribute("aria-pressed", String(!wasLiked));
      heart.setAttribute(
        "aria-label",
        `${wasLiked ? "Like" : "Unlike"} this book`
      );
      heart.title = wasLiked
        ? "Add to liked books"
        : "Remove from liked books";
    });

    // Refresh the dedicated liked-books page only if it is visible.
    if (!likedView.classList.contains("hidden")) {
      await renderLikedBooks();
    }

    // Populate recommendations on the first like only if empty.
    if (!wasLiked) {
      await loadRecommendationsIfEmpty();
    }

  } catch (error) {
    console.error("Could not update like:", error);
  } finally {
    button.disabled = false;
  }
});



async function renderLikedBooks() {
  const likedGrid = document.getElementById("likedGrid");
  if (!likedGrid) return;

  try {
    const response = await fetch("/api/likes");
    if (!response.ok) throw new Error("Could not load liked books.");

    const books = await response.json();
    window.__likedBooks = books;

    likedGrid.innerHTML = books.length
      ? books.map(book => bookCard(book)).join("")
      : `<p class="empty-state">You haven't liked any books yet. Click ♥ on a book to save it.</p>`;
  } catch (error) {
    console.error("Liked books error:", error);
    likedGrid.innerHTML =
      `<p class="empty-state">Could not load your liked books.</p>`;
  }
}



let recommendationsLoading = false;

async function loadRecommendationsIfEmpty() {
  const grid = document.getElementById("personalizedGrid");
  if (!grid || recommendationsLoading) return;

  // Keep existing recommendations unchanged.
  if (grid.querySelector(".book-card")) return;

  recommendationsLoading = true;

  try {
    await renderPersonalizedRecommendations();
  } finally {
    recommendationsLoading = false;
  }
}

async function initializeBookMatch() {
  await loadLikedBooks();
  await renderHome();
  await renderPersonalizedRecommendations();
}

initializeBookMatch();


async function renderPersonalizedRecommendations() {
    const grid = document.getElementById("personalizedGrid");

    if (!grid) return;

    try {
        const response = await fetch("/api/recommendations/personalized");

        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }

        const books = await response.json();
        window.__personalizedBooks = books;

        // No recommendations: keep the grid empty.
        // The empty message is handled by the HTML.
        if (!books.length) {
            grid.innerHTML = "";
            updatePersonalizedSection();
            return;
        }

        // Render recommendation cards.
        grid.innerHTML = books.map((book, index) => `
            <article class="book-card">
                ${likeButtonHTML(book)}

                <button
                    class="book-card-button personalized-book-button"
                    type="button"
                    data-recommendation-index="${index}"
                >
                    ${coverHTML(
                  book,
                  "book-cover",
                  `${getAwardBadge(book)}${getBestsellerBadge(book)}`
              )}

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
                    </span>
                </button>
            </article>
        `).join("");

        updatePersonalizedSection();

    } catch (error) {
        console.error("Personalized recommendations error:", error);

        grid.innerHTML = `
            <p class="empty-state">Could not load recommendations.</p>
        `;
    }
}



document.getElementById("personalizedGrid").addEventListener("click", event => {
  // Let the existing like-button handler handle hearts.
  if (event.target.closest(".like-button")) return;

  const cardButton = event.target.closest(".book-card-button");
  if (!cardButton) return;

  const googleId = cardButton.dataset.bookId;

  const book = (window.__personalizedBooks || []).find(
    item => String(item.google_id || item.id || "") === String(googleId)
  );

  if (book) {
    openBook(book);
  } else {
    console.error("Could not find the selected recommendation:", googleId);
  }
});



function getAwardBadge(book) {
  const isWinner =
    book.is_award_winner === true ||
    book.is_award_winner === 1 ||
    (typeof book.is_award_winner === "string" &&
      ["true", "1"].includes(
        book.is_award_winner.trim().toLowerCase()
      ));

  if (!isWinner) return "";

  let awardNames = book.award_names || "";

  // Convert a string representation of a Python list into an array
  if (typeof awardNames === "string") {
    try {
      awardNames = JSON.parse(
        awardNames.replace(/'/g, '"')
      );
    } catch {
      awardNames = [awardNames];
    }
  }

  if (!Array.isArray(awardNames)) {
    awardNames = [awardNames];
  }

  const awardName = awardNames
    .filter(Boolean)
    .map(name =>
      name
        .replace(/–winning works/gi, "")
        .replace(/winning works/gi, "")
        .trim()
    )
    .join(", ");

  if (!awardName) return "";


return `
  <span
    class="award-stamp"
    title="${escapeHTML(awardName)}"
  >
    <span class="award-icon">★</span>
    <span class="award-divider"></span>
    <span class="award-name">
      ${escapeHTML(awardName)}
    </span>
  </span>
`;
}

function showView(view) {
  [homeView, searchView, detailView, likedView].forEach(v => {
    v.classList.add("hidden");
  });
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




async function getDiscoverBooks(
    count = 20,
    category = state.currentCategory
) {
    const params = new URLSearchParams({
        count: String(count),
        category: category || "All"
    });

    const response = await fetch(
        `${API_CONFIG.discover}?${params.toString()}`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to load books: HTTP ${response.status}`
        );
    }

    const books = await response.json();

    if (!Array.isArray(books)) {
        throw new Error(
            "Discover API did not return a list of books."
        );
    }

    return books;
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

    const visibleBooks = books.slice(0, 17);

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
      ${coverHTML(book, "result-cover", getAwardBadge(book), getBestsellerBadge(book))}

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
          ${coverHTML(book, "result-cover", getAwardBadge(book), getBestsellerBadge(book))}

          <span class="search-result-info">
            ${book.is_award_winner ? `
            <span class="search-award-label">
              ★ ${escapeHTML(
                String(book.award_names || "")
                  .replace(/[\[\]'"]/g, "")
                  .replace(/–winning works|winning works/gi, "")
                  .trim())}
            </span>
          ` : ""}
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

console.log("Selected book:", book);
console.log("Google Books URL:", book.google_books_url);

selectedBook.innerHTML = `
  <div class="selected-book-layout">
  <div class="selected-cover-wrap">
    ${coverHTML(book, "selected-cover", getAwardBadge(book), getBestsellerBadge(book))}
  </div>

  <div class="selected-content">
      <div class="selected-title-row">
        <h1>${escapeHTML(book.title || "")}</h1>
        ${likeButtonHTML(book)}
      </div>

    <p class="selected-author">
        By ${escapeHTML(firstAuthor(book.authors))}
    </p>

    <div class="selected-book-badges">
    ${getAwardBadge(book)}
    ${getBestsellerBadge(book)}
</div>

      ${book.google_books_url ? `
    <a
        href="${book.google_books_url}"
        target="_blank"
        rel="noopener noreferrer"
        class="google-books-link"
    >
        <i class="fas fa-external-link-alt"></i>
        View on Google Books
    </a>
` : ""}

      <p class="selected-description">
        ${escapeHTML(book.description || "No description available.")}
      </p>

      <p class="selected-category">
        ${escapeHTML(firstCategory(book.categories))}
      </p>
    </div>
  </div>
`;


id.innerHTML = recommendations.length
  ? recommendations.map((book, index) => `
      <article class="book-card">
        <button
          class="book-card-button recommendation-button"
          type="button"
          data-recommendation-index="${index}"
        >
          ${coverHTML(book,"book-cover", getAwardBadge(book), getBestsellerBadge(book))}

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
          ${coverHTMLrecommendationGrL(book,"book-cover", getAwardBadge(book), getBestsellerBadge(book))}

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


function googleBooksUrl(googleId) {
    if (
        !googleId ||
        ["nan", "none", "null"].includes(
            String(googleId).trim().toLowerCase()
        )
    ) {
        return null;
    }

    return `https://books.google.com/books?id=${encodeURIComponent(
        String(googleId).trim()
    )}`;
}


async function openBook(book, addToHistory = true) {
  if (!book) return;

  const visibleView = [homeView, searchView, likedView, detailView]
    .find(view => !view.classList.contains("hidden"));

  if (visibleView === detailView) {
    if (
      addToHistory &&
      state.currentBook &&
      String(state.currentBook.google_id ?? state.currentBook.id) !==
        String(book.google_id ?? book.id)
    ) {
      state.detailHistory.push(state.currentBook);
    }
  } else {
    state.detailHistory = [];
    state.detailReturnView = visibleView || homeView;
  }

  state.currentBook = book;
  searchDropdown.classList.add("hidden");

  selectedBook.innerHTML = `
    <div class="selected-book-layout">
      <div class="selected-cover-wrap">
        ${coverHTML(
          book,
          "selected-cover",
          `${getAwardBadge(book)}${getBestsellerBadge(book)}`
        )}
      </div>

      <div class="selected-content">
    <div class="selected-title-row">
        <h1>${escapeHTML(book.title || "")}</h1>
        ${likeButtonHTML(book)}
    </div>

    <p class="selected-author">
        By ${escapeHTML(firstAuthor(book.authors))}
    </p>
      
    ${googleBooksUrl(book.google_id)
    ? `<a
         class="google-books-link"
         href="${googleBooksUrl(book.google_id)}"
         target="_blank"
         rel="noopener noreferrer"
       >View on Google Books ↗</a>`
    : ""}

      <p class="selected-description">
        ${escapeHTML(book.description || "No description available.")}
      </p>

      <p class="selected-category">
        ${escapeHTML(firstCategory(book.categories))}
      </p>
      </div>
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
    ${likeButtonHTML(recommendedBook)}

    <button
      class="book-card-button recommendation-button"
      type="button"
      data-recommendation-index="${index}"
    >
      ${coverHTML(
    recommendedBook,
    "book-cover",
    `${getAwardBadge(recommendedBook)}${getBestsellerBadge(recommendedBook)}`
)}

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
        ${scoreToPercent(recommendedBook.final_score ?? recommendedBook.similarity)}
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





let categoryRequestId = 0;

const categoryFilters = document.getElementById("categoryFilters");
categoryFilters.scrollLeft = 0;

categoryFilters.addEventListener("click", async (event) => {
    const button = event.target.closest(".category");

    if (!button || !categoryFilters.contains(button)) return;

    console.log("Clicked category:", button.dataset.category);

    if (button.classList.contains("active")) return;

    const requestId = ++categoryRequestId;

    categoryFilters.querySelectorAll(".category").forEach(item => {
        item.classList.toggle("active", item === button);
    });

    state.currentCategory = button.dataset.category;

    try {
        const books = await getDiscoverBooks(
            20,
            state.currentCategory
        );

        if (requestId !== categoryRequestId) return;

        window.__discoverBooks = books;

        const visibleBooks = books.slice(0, 17);

        homeGrid.innerHTML = visibleBooks.length
            ? visibleBooks.map(book => bookCard(book)).join("")
            : `<div class="empty-state">
                   No books found in this category.
               </div>`;
    } catch (error) {
        if (requestId !== categoryRequestId) return;

        console.error("Category loading error:", error);
        homeGrid.innerHTML = `<div class="empty-state">
            Could not load books. Check the console for details.
        </div>`;
    }
});



likedButton?.addEventListener("click", async () => {
  await loadLikedBooks();
  await renderLikedBooks();
  showView(likedView);
});

backFromLiked?.addEventListener("click", () => {
  showView(homeView);
});


$("#backHome").addEventListener("click", () => {
  const previousBook = state.detailHistory.pop();

  if (previousBook) {
    openBook(previousBook, false);
    return;
  }

  const returnView = state.detailReturnView || homeView;
  state.detailReturnView = null;
  state.currentBook = null;
  showView(returnView);
});

$("#backHomeFromSearch").addEventListener("click", () => {
  showView(homeView);
});


const personalizedGrid = document.getElementById("personalizedGrid");

if (personalizedGrid) {
  personalizedGrid.addEventListener("click", event => {
    // The heart has its own click handler.
    if (event.target.closest(".like-button")) return;

    const button = event.target.closest(".personalized-book-button");
    if (!button) return;

    const index = Number(button.dataset.recommendationIndex);
    const book = window.__personalizedBooks?.[index];

    if (!book) {
      console.error("Recommendation not found at index:", index);
      return;
    }

    openBook(book);
  });
}



// Load saved likes first, then display the books.
async function initializeBookMatch() {
  try {
    await loadLikedBooks();
  } catch (error) {
    console.error("Could not initialize liked books:", error);
  }

  await renderHome();
  await renderPersonalizedRecommendations();
}

initializeBookMatch();
