document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const resultsContainer = document.getElementById('results');

    const performSearch = async (query) => {
        try {
            resultsContainer.innerHTML = '<p>Loading...</p>';
            
            const response = await fetch(`/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.success) {
                renderProducts(data.products);
            } else {
                resultsContainer.innerHTML = `<p>Error: ${data.error}</p>`;
            }
        } catch (error) {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<p>An error occurred while searching.</p>';
        }
    };

    const renderProducts = (products) => {
        if (products.length === 0) {
            resultsContainer.innerHTML = '<p>No products found.</p>';
            return;
        }

        resultsContainer.innerHTML = products.map(product => `
            <div class="product-card">
                <img 
                    src="${product.image_url || 'placeholder.jpg'}" 
                    alt="${product.name}"
                >
                <div class="product-details">
                    <h3 class="product-name">${product.name}</h3>
                    <p class="product-price">
                        $${product.current_price ? product.current_price.toFixed(2) : 'N/A'}
                    </p>
                    <p class="price-change ${
                        product.price_change > 0 ? 'price-increase' : 
                        product.price_change < 0 ? 'price-decrease' : ''
                    }">
                        ${product.price_change > 0 ? '▲' : product.price_change < 0 ? '▼' : ''}
                        ${Math.abs(product.price_change_pct).toFixed(2)}%
                    </p>
                </div>
            </div>
        `).join('');
    };

    searchBtn.addEventListener('click', () => performSearch(searchInput.value));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch(searchInput.value);
    });
});