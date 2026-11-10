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
					// The code language starts as the reader's stored pick, else the
					// page language (<html lang>), else English. A language with no
					// snippet variant has no CSS rule, so English shows.
					tag: 'script',
					content:
						"(()=>{var d=document.documentElement,l=null;try{l=localStorage.getItem('legesher-snippet-lang');}catch(e){}if(!l)l=(d.lang||'en').split('-')[0].toLowerCase();if(l!=='en')d.dataset.snippetLang=l;})();",
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
						{
							label: 'Playground',
							translations: { es: 'Zona de pruebas', ar: 'ساحة التجريب' },
							slug: 'playground',
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
