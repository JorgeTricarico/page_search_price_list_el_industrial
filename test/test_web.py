import pytest
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

@pytest.fixture(scope="session")
def base_url():
    # URL de la web a probar.
    return "https://lista-precio-el-industrial-dev.netlify.app/"

def test_product_list_and_footer(base_url):
    # Se genera el string esperado en el footer basado en la fecha actual.
    today_str = datetime.now().strftime("%d-%m-%y")
    expected_footer_text = f"Según Lista {today_str}"
    
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

        # Verificamos que exista al menos un producto.
        # Asumimos que los productos se listan en filas de una tabla (<tr>) dentro de <tbody>.
        product_rows = page.locator("table tbody tr")
        if product_rows.count() == 0:
            # En caso de que no se usen tablas, se puede probar con otro selector.
            product_rows = page.locator(".product")
        assert product_rows.count() > 0, "No se encontraron productos en la página."

        # Verificamos el footer.
        # Se asume que el footer se encuentra en un elemento <footer>.
        footer_locator = page.locator("footer")
        if footer_locator.count() == 0:
            # Si no hay <footer>, buscamos directamente el texto esperado.
            footer_locator = page.locator(f"text={expected_footer_text}")
            assert footer_locator.count() > 0, f"No se encontró el footer con el texto esperado '{expected_footer_text}'."
        else:
            footer_text = footer_locator.text_content()
            assert expected_footer_text in footer_text, (
                f"El footer no contiene el texto esperado. Se esperaba '{expected_footer_text}', "
                f"pero se encontró '{footer_text}'."
            )
        
        browser.close()
