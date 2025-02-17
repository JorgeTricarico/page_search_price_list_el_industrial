import pytest
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

@pytest.fixture(scope="session")
def base_url():
    # URL de la web a probar.
    return "https://lista-precio-el-industrial-dev.netlify.app/"

def test_product_list(base_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Accedemos a la web.
        page.goto(base_url)
        
        # Esperamos a que se carguen elementos característicos (por ejemplo, el encabezado de la tabla).
        page.wait_for_selector("text=Producto", timeout=15000)
        
        # Si la web muestra un mensaje de "Cargando productos...", esperamos a que desaparezca.
        try:
            page.wait_for_selector("text=Cargando productos...", state="detached", timeout=15000)
        except PlaywrightTimeoutError:
            # En caso de timeout, seguimos con la verificación.
            pass

        # Verificamos que existan al menos dos productos con el atributo data-label="Producto".
        product_elements = page.locator('td[data-label="Producto"]')
        assert product_elements.count() >= 2, "No se encontraron al menos dos productos en la página."

        browser.close()
