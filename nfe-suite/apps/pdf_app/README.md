# PDF ➜ Chaves de Acesso (NF-e)

- Envie um `.zip` com PDFs.
- Lemos **todas as páginas** de cada PDF, extraímos **todas as chaves de 44 dígitos**, removemos **duplicatas**.
- Tabelas: **Resumo por arquivo** e **Linhas por chave** (para exportar CSV/Excel).

## Dependências nativas (no SO)
- `poppler-utils` (para `pdf2image`)
- `libzbar0` (para `pyzbar`)
No Azure, use o `Dockerfile` fornecido.
