# Designeo Site Studio

Ferramenta local para planeamento, geração de conteúdo e publicação de websites WordPress.

## Instalação

```bash
cd designeo-studio
pip install -r requirements.txt
python app.py
```

Abre o browser em: **http://localhost:5050**

## Configuração

1. Introduz a tua **Claude API key** na barra lateral (guardada localmente, nunca enviada a nenhum servidor)
2. Para ligar a um site WordPress, vai ao separador **WordPress** de cada cliente e segue as instruções para criar uma Application Password

## Funcionalidades

### Módulo 1 — Briefing & Plano
- Briefing estruturado por cliente
- Geração automática de plano completo (sitemap, secções, copy de arranque, SEO)
- Multi-cliente com dados guardados em `clients.json`

### Módulo 2 — Conteúdo completo
- Geração de copy completo página a página ou todas de uma vez
- Copy final com headline, corpo, listas, CTAs e notas para o Elementor
- SEO final (meta title + meta description) pronto a usar

### Módulo 3 — WordPress
- Ligação via Application Passwords (nativo no WP 5.6+)
- Publicação de páginas directamente como rascunho
- Link directo para editar no wp-admin após publicação

## Estrutura de ficheiros

```
designeo-studio/
├── app.py           ← servidor Flask
├── index.html       ← interface React
├── clients.json     ← dados dos clientes (criado automaticamente)
└── requirements.txt
```
