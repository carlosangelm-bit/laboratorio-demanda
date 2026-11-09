# Laboratorio de demanda

Herramienta para cruzar ventas internas con fuentes públicas de México. Las ventas se suben desde el navegador y **no se guardan en ningún servidor**; las fuentes públicas se descargan solas cada lunes.

- La página vive en `docs/index.html` y se publica con GitHub Pages.
- La rutina `.github/workflows/actualizar.yml` corre cada lunes (o a mano desde la pestaña Actions), ejecuta `scripts/actualizar.py` y vuelve a publicar.
- Los datos públicos quedan en `docs/data/externos.json`.

## Puesta en marcha (una sola vez)

1. **Activar la página.** Settings → Pages → Source: *GitHub Actions*.
2. **Agregar las claves** en Settings → Secrets and variables → Actions → *New repository secret*:
   - `DENUE_TOKEN`: se obtiene gratis en https://www.inegi.org.mx/app/api/denue/tokenVerify/tokenverify.html
   - `BANXICO_TOKEN`: se obtiene gratis en https://www.banxico.org.mx/SieAPIRest/service/v1/token
3. **Elegir las series de Banxico.** En el cuadro CF958 del SIE, copia la clave (empieza con `SF`) de la serie que interese, por ejemplo ventas al detalle, y ponla en `banxico_series` dentro de `config.json`.
4. En la pestaña Actions, abre *Actualizar datos y publicar* y presiona *Run workflow*.

## Fuentes sin API

Pega los datos en la carpeta `datos_manuales/` respetando los encabezados y se cargarán solos en la siguiente corrida:

| Archivo | Columnas | Fuente sugerida |
| --- | --- | --- |
| `poblacion.csv` | estado, poblacion, ingreso | Censo 2020 y ENIGH 2024 |
| `gasto_estatal.csv` | fecha, estado, valor | BBVA Research, consumo con tarjeta por entidad |
| `clima.csv` | fecha, estado, temp | SMN, temperatura máxima |

El estado puede ir con nombre, abreviatura o clave INEGI (1 a 32). Las fechas, como `2026-01-05` o `05/01/2026`.

## Qué tiendas cuenta el DENUE

`config.json` define las actividades: `46111` (abarrotes y misceláneas) y `46211` (supermercados y minisupers). Se pueden cambiar por otras claves SCIAN.
