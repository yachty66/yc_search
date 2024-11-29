const _supabase = window.supabaseClient;

let currentPage = 0; // Track the current page
const itemsPerPage = 10; // Number of items to load per page
let isLoading = false; // Prevent multiple loads
let currentQuery = ""; // Variable to store the current query

// Add a flag to track if we're currently showing query results
let isShowingQueryResults = false;

// Function to load HTML content
function loadHTML(url, elementId) {
  fetch(url)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.text();
    })
    .then((data) => {
      document.getElementById(elementId).innerHTML = data;

      // If loading companies.html, also fetch the company data
      if (elementId === "companies-section") {
        loadCompanyData(); // Load company data
        setupSearchFunctionality(); // Set up search functionality
      }
    })
    .catch((error) => console.error("Error loading HTML:", error));
}

async function loadCompanyDataFromQuery(query) {
  const companiesGrid = document.getElementById("companies-grid");

  // Show loading spinner
  companiesGrid.innerHTML = `
        <div class="col-span-full flex justify-center items-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <span class="ml-3 text-gray-600">Searching companies...</span>
        </div>
    `;

  try {
    const response = await fetch("/api/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        page: currentPage,
        limit: itemsPerPage,
      }),
    });

    // Parse the JSON response
    const data = await response.json();

    // Clear the loading spinner
    companiesGrid.innerHTML = "";

    // Handle empty results
    if (!data || data.length === 0) {
      companiesGrid.innerHTML = `
                <div class="col-span-full text-center py-10">
                    <p class="text-gray-600">No companies found matching your search.</p>
                </div>
            `;
      return;
    }

    // Render company cards
    data.forEach((company) => {
      const companyCard = document.createElement("div");
      companyCard.className =
        "bg-white p-4 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300";

      // Create a Set to filter out duplicate tags
      const uniqueTags = [...new Set(company.tags)];
      const blueTags = uniqueTags.filter((tag) => tag !== "Active");

      companyCard.innerHTML = `
                <div class="flex flex-col items-center">
                    <img src="${company.logo}" alt="${
        company.company_name
      } Logo" 
                         class="w-24 h-24 rounded-lg mb-3 border border-gray-200">
                    <div class="text-center">
                        <h3 class="font-semibold text-lg text-gray-900">${
                          company.company_name
                        }</h3>
                        <div class="flex flex-wrap gap-1 justify-center">
                            ${blueTags
                              .map(
                                (tag) => `
                                    <span class="text-xs bg-blue-100 text-blue-800 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors">
                                        ${tag}
                                    </span>
                                `
                              )
                              .join("")}
                        </div>
                    </div>
                </div>
            `;

      companiesGrid.appendChild(companyCard);
    });
  } catch (error) {
    console.error("Error loading companies:", error);
    companiesGrid.innerHTML = `
            <div class="col-span-full text-center py-10">
                <p class="text-red-600">Error loading companies. Please try again.</p>
            </div>
        `;
  }
}

async function loadCompanyDataWithoutQuery() {
  if (isLoading) return; // Prevent loading if already in progress
  isLoading = true; // Set loading state

  const start = currentPage * itemsPerPage; // Calculate start index
  const end = start + itemsPerPage - 1; // Calculate end index

  try {
    const { data, error } = await _supabase
      .from("startuprxiv") // Replace with your table name
      .select("*") // Select the columns you need
      .range(start, end); // Implement pagination

    if (error) throw error;

    const companiesGrid = document.getElementById("companies-grid");

    // Loop through each company and create a card
    data.forEach((company) => {
      const companyCard = document.createElement("div");
      companyCard.className =
        "bg-white p-4 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300";

      // Create a Set to filter out duplicate tags
      const uniqueTags = [...new Set(company.tags)];

      // Filter tags to only include those that are not "Active"
      const blueTags = uniqueTags.filter((tag) => tag !== "Active");

      // Create the card content
      companyCard.innerHTML = `
                <div class="flex flex-col items-center">
                    <img src="${company.logo}" alt="${
        company.company_name
      } Logo" class="w-24 h-24 rounded-lg mb-3 border border-gray-200">
                    <div class="text-center">
                        <h3 class="font-semibold text-lg text-gray-900">${
                          company.company_name
                        }</h3>
                        <div class="flex flex-wrap gap-1 justify-center">
                            ${blueTags
                              .map(
                                (tag) => `
                                <span class="text-xs bg-blue-100 text-blue-800 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors">${tag}</span>
                            `
                              )
                              .join("")}
                        </div>
                    </div>
                </div>
            `;

      companiesGrid.appendChild(companyCard);
    });

    currentPage++; // Increment the current page
  } catch (error) {
    console.error("Error fetching company data:", error);
  } finally {
    isLoading = false; // Reset loading state
  }
}

// Function to load company data from Supabase
async function loadCompanyData(query) {
  if (query) {
    // Only load query results if triggered by search button
    if (!isShowingQueryResults) {
      isShowingQueryResults = true;
      await loadCompanyDataFromQuery(query);
    }
  } else {
    // Reset flag when loading without query
    isShowingQueryResults = false;
    await loadCompanyDataWithoutQuery();
  }
}

// Function to set up search functionality
function setupSearchFunctionality() {
  const searchButton = document.getElementById("search-button");
  const searchBar = document.getElementById("search-bar");

  searchButton.addEventListener("click", () => {
    currentQuery = searchBar.value;
    // Reset the flag to allow new query search
    isShowingQueryResults = false;
    currentPage = 0; // Reset pagination
    loadCompanyData(currentQuery);
  });
}

// Handle scroll event to load more data
function handleScroll() {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
    // Only load more if not showing query results
    if (!isShowingQueryResults) {
      loadCompanyData(currentQuery);
    }
  }
}

// Add scroll event listener
window.addEventListener("scroll", handleScroll);

// Load the landing and companies sections
loadHTML("landing.html", "landing-section");
loadHTML("companies.html", "companies-section");
