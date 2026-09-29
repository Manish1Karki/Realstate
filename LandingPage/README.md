# Land Discover landing page

The landing page sends visitors to the public property dashboard through the prominent **Browse properties** and **Search listings** actions. Browsing does not require sign-in.

For local development, the dashboard defaults to `http://127.0.0.1:8000/`. To use another address, copy `.env.example` to `.env` and set:

```env
VITE_DASHBOARD_URL=https://your-dashboard.example/
```

Run the landing page with `npm run dev`. Run the FastAPI aggregator separately on port 8000.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
