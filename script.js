document.addEventListener("DOMContentLoaded", async () => {
  const productTable = document.querySelector("#productTable tbody");
  const searchInput = document.getElementById("searchInput");
  const loader = document.getElementById("loader");
  const themeToggle = document.getElementById("themeToggle");
  const dollarPriceElement = document.getElementById("dollarPrice");
  const fechaListaElement = document.getElementById("fechaLista");

  let currentJsonFileName = "";
  let searchTimeout;
  let products = [];

  const getLatestJsonFileName = async () => {
      try {
          console.log("Obteniendo nombre del archivo JSON desde /price-lists-json/latest-json-filename.txt (carpeta price-lists-json)...");
          const response = await fetch("/price-lists-json/latest-json-filename.txt");
          if (!response.ok) {
              throw new Error("No se pudo obtener el nombre del archivo JSON desde /price-lists-json/latest-json-filename.txt");
          }
          const latestFile = await response.text();
          console.log("Nombre del archivo JSON obtenido desde /price-lists-json/latest-json-filename.txt:", latestFile.trim());
          return latestFile.trim();
      } catch (error) {
          console.error("Error al obtener el nombre del JSON desde /price-lists-json/latest-json-filename.txt:", error);
          throw error;
      }
  };

  const fetchDollarPrice = async () => {
      try {
          const response = await fetch("https://dolarapi.com/v1/ambito/dolares/oficial");
          const data = await response.json();
          console.log(data);
          dollarPriceElement.textContent = `$${data.venta.toFixed(2)}`;
      } catch (error) {
          console.error("Error al obtener el precio del dólar:", error);
          dollarPriceElement.textContent = "N/A";
      }
  };

  const fetchAndDecompressProducts = async () => {
      console.log("Fetching and decompressing products from:", `/price-lists-json/${currentJsonFileName}`);
      loader.classList.remove("hidden");
      try {
          const response = await fetch(`/price-lists-json/${currentJsonFileName}`);
           // Verificar la codificación de la respuesta
          console.log("Content-Type:", response.headers.get("Content-Type"));

          if (!response.ok) {
              throw new Error("Network response was not ok");
          }

          const compressedStream = response.body.pipeThrough(new DecompressionStream("gzip"));
          const reader = compressedStream.getReader();
          const decoder = new TextDecoder("utf-8");
          let jsonText = "";

          while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              try {
                  jsonText += decoder.decode(value, { stream: true });
              } catch (decodeError) {
                  console.error("Error al decodificar:", decodeError);
                  break;
              }
          }
          jsonText += decoder.decode();

          // Inspeccionar el JSON antes de parsear
          console.log("JSON Descomprimido:", jsonText);

          try {
              products = JSON.parse(jsonText);
              localStorage.removeItem("products");
              localStorage.removeItem("jsonFileName");
              localStorage.setItem("products", JSON.stringify(products));
              localStorage.setItem("jsonFileName", currentJsonFileName);
              displayProducts(products);
          } catch (jsonError) {
              console.error("Error al analizar JSON:", jsonError);
              // Aquí puedes agregar un mensaje al usuario o tomar otra acción
          }
      } catch (error) {
          console.error("Error al cargar los productos:", error);
      }
      loader.classList.add("hidden");
  };

  const displayProducts = (productsToDisplay) => {
      productTable.innerHTML = "";
      if (productsToDisplay.length === 0) {
          const row = document.createElement("tr");
          const cell = document.createElement("td");
          cell.colSpan = 5;
          cell.textContent = "No se ha encontrado el producto.";
          cell.style.textAlign = "center";
          row.appendChild(cell);
          productTable.appendChild(row);
          return;
      }
      productsToDisplay.forEach((product) => {
          const row = document.createElement("tr");
          // Utilizar textContent para evitar la interpretación de HTML
          row.innerHTML = `
              <td data-label="Producto">${escapeHTML(product.producto)}</td>
              <td data-label="Detalle">${escapeHTML(product.detalle)}</td>
              <td data-label="Marca">${escapeHTML(product.marca)}</td>
              <td data-label="Un/Mts">${product.unidad === "UN" ? "Un" : "Mts"}</td>
              <td data-label="Precio">${product.moneda} ${escapeHTML(product.precio)}</td>
          `;

          productTable.appendChild(row);
      });
  };

  // Función para escapar caracteres HTML
  const escapeHTML = (str) => {
      if (!str) return '';
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  };

  const filterProducts = (searchTerm) => {
      const searchTerms = searchTerm.toLowerCase().split(/\s+/).filter(Boolean);
      return products.filter((product) =>
          searchTerms.every(
              (term) =>
                  product.producto.toLowerCase().includes(term) ||
                  product.detalle.toLowerCase().includes(term) ||
                  product.marca.toLowerCase().includes(term)
          )
      );
  };

  const initializeProducts = async () => {
      try {
          currentJsonFileName = await getLatestJsonFileName();
      } catch (error) {
          console.error("No se pudo obtener el nombre del archivo JSON.");
          loader.classList.add("hidden");
          return;
      }
      if (!currentJsonFileName) {
          console.error("No hay archivo JSON disponible para cargar los productos.");
          loader.classList.add("hidden");
          return;
      }

      const storedJsonFileName = localStorage.getItem("jsonFileName");
      if (storedJsonFileName === currentJsonFileName) {
          const storedProducts = localStorage.getItem("products");
          products = JSON.parse(storedProducts);
          displayProducts(products);
          console.log("Usando productos cacheados para el archivo:", currentJsonFileName);
      } else {
          await fetchAndDecompressProducts();
      }
      displayDate();
  };

  searchInput.addEventListener("input", () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
          const searchTerm = searchInput.value.trim();
          const filteredProducts = searchTerm ? filterProducts(searchTerm) : products;
          displayProducts(filteredProducts);
      }, 400);
  });

  themeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      themeToggle.innerHTML = document.body.classList.contains("dark-mode") ? "☀️" : "";
      themeToggle.style.backgroundColor = document.body.classList.contains("dark-mode") ? "#2e2e2e" : "#fafafa";
  });

  const extractDateFromFileName = (fileName) => {
      const datePattern = /(\d{2}-\d{2}-\d{2,4})/;
      const match = fileName.match(datePattern);
      return match ? match[0] : null;
  };

  const displayDate = () => {
      const fechaExtraida = extractDateFromFileName(currentJsonFileName);
      if (fechaListaElement) {
          if (fechaExtraida) {
              fechaListaElement.textContent = `Según Lista ${fechaExtraida}`;
              fechaListaElement.style.fontSize = "small";
              fechaListaElement.style.textAlign = "center";
          }
      }
  };

  await initializeProducts();
  fetchDollarPrice();
  searchInput.focus();
});
