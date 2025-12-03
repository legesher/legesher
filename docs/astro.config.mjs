// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'Legesher Documentation',
			social: {
				github: 'https://github.com/legesher/legesher',
			},
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Quick Start', slug: 'getting-started' },
						{ label: 'Privacy Policy', slug: 'privacy' },
					],
				},
				{
					label: 'Project',
					items: [
						{ label: 'Planning Summary', slug: 'planning_summary' },
					],
				},
				{
					label: 'Specifications',
					items: [
						{ label: 'MLCP v1.0', slug: 'specifications/mlcp-v1' },
					],
				},
				{
					label: 'Architecture',
					items: [
						{ label: 'Implementation Roadmap', slug: 'architecture/implementation-roadmap' },
						{ label: 'Language Pack Registry', slug: 'architecture/language-pack-registry' },
					],
				},
				{
					label: 'Guides',
					items: [
						{ label: 'Example Guide', slug: 'guides/example' },
					],
				},
				{
					label: 'Reference',
					autogenerate: { directory: 'reference' },
				},
			],
		}),
	],
});
