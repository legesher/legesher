// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import vercel from '@astrojs/vercel';

// https://astro.build/config
export default defineConfig({
	site: 'https://docs.legesher.io',
	output: 'static',
	adapter: vercel(),
	integrations: [
		starlight({
			title: 'Legesher Documentation',
			customCss: ['./src/styles/custom.css'],
			logo: {
				src: './src/assets/Peggy-Headshot.svg',
				alt: 'Legesher',
			},
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/legesher/legesher' },
			],
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Why Legesher?', slug: 'why-legesher' },
						{ label: 'Quick Start', slug: 'getting-started' },
					],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'Supported Languages', slug: 'reference/supported-languages' },
						{ label: 'Privacy Policy', slug: 'privacy' },
					],
				},
			],
		}),
	],
});
