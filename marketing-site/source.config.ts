import { defineConfig, defineDocs } from 'fumadocs-mdx/config';

export default defineConfig({
  mdxOptions: {},
});

export const { docs, meta } = defineDocs({
  dir: 'src/content/docs',
});
