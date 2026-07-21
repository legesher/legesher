// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import vercel from '@astrojs/vercel';
import { legesherSnippets } from './integrations/legesher-snippets.mjs';

// https://astro.build/config
export default defineConfig({
	site: 'https://docs.legesher.io',
	output: 'static',
	adapter: vercel(),
	integrations: [
		legesherSnippets(),
		starlight({
			title: 'Legesher Documentation',
			customCss: ['./src/styles/custom.css'],
			components: {
				SocialIcons: './src/components/SnippetLangSelect.astro',
			},
			head: [
				{
					tag: 'script',
					content:
						"(()=>{try{var l=localStorage.getItem('legesher-snippet-lang');if(l&&l!=='en')document.documentElement.dataset.snippetLang=l;}catch(e){}})();",
				},
			],
			logo: {
				src: './src/assets/Peggy-Headshot.svg',
				alt: 'Legesher',
			},
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/legesher/legesher' },
			],
			locales: {
				root: { label: 'English', lang: 'en' },
				es: { label: 'Español', lang: 'es' },
				ar: { label: 'العربية', lang: 'ar', dir: 'rtl' },
			},
			sidebar: [
				{
					label: 'Getting Started',
					translations: { es: 'Primeros pasos', ar: 'البدء' },
					items: [
						{
							label: 'Why Legesher?',
							translations: { es: '¿Por qué Legesher?', ar: 'لماذا Legesher؟' },
							slug: 'why-legesher',
						},
						{
							label: 'Quick Start',
							translations: { es: 'Inicio rápido', ar: 'البدء السريع' },
							slug: 'getting-started',
						},
					],
				},
				{
					label: 'Reference',
					translations: { es: 'Referencia', ar: 'المرجع' },
					items: [
						{
							label: 'Supported Languages',
							translations: { es: 'Idiomas compatibles', ar: 'اللغات المدعومة' },
							slug: 'reference/supported-languages',
						},
						{
							label: 'Privacy Policy',
							translations: { es: 'Política de privacidad', ar: 'سياسة الخصوصية' },
							slug: 'privacy',
						},
					],
				},
			],
		}),
	],
});
