React/Tailwind/shadcn setup notes
---------------------------------
- The existing project is a Django app without a JavaScript toolchain. React, TypeScript, Tailwind CSS, and shadcn components will need to be bootstrapped before the new UI can render.
- Default component path: we created /components/ui to match shadcn conventions. Keep shared UI pieces here so future shadcn CLI runs can drop new components into the same folder.
- Default styles path: create /styles (or app/globals.css if using Next.js) and point Tailwind's content sources at ./components/**/*.{ts,tsx} plus your templates/pages.

Suggested bootstrap commands
- npm init -y
- npm install react react-dom typescript tailwindcss postcss autoprefixer lucide-react
- npx tailwindcss init -p
- npx shadcn-ui init --defaults --components components/ui

Post-bootstrap configuration
- In tsconfig.json set "baseUrl": "." and paths alias: { "@/*": ["./*"] } so imports like "@/components/ui/modern-side-bar" resolve.
- Tailwind content should include: "./components/**/*.{ts,tsx}", "./pages/**/*.{js,ts,jsx,tsx}", "./app/**/*.{js,ts,jsx,tsx}", and any Django templates if you render React via Django.
- Import the generated Tailwind layer into styles/globals.css (or static/css/base.css if you prefer to co-locate styles) and ensure the stylesheet is loaded by your bundler.

Component usage
- The sidebar component lives at /components/ui/modern-side-bar.tsx with a demo at /components/ui/demo.tsx.
- It expects lucide-react icons and Tailwind utility classes to be available. Provide React context/bundler as usual; no extra providers are required.
- For assets, swap placeholder initials/logo with your own or safe stock images (e.g., https://images.unsplash.com/... from Unsplash) if you add avatars or brand marks later.
