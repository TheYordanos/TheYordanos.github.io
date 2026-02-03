package main

import "core:os"
import "core:os/os2"
import "core:fmt"
import "core:strings"

import cm "vendor:commonmark"

default_output: string = "posts"
default_input: string = "markdown"

post_header: string = `
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Post</title>

	<link rel="stylesheet" type="text/css" href="./../../style/style.css">

	<link rel="stylesheet" href="./../../style/highlight/hl.css">
	<script src="./../../style/highlight/highlight.pack.js"></script>
	<script>hljs.initHighlightingOnLoad();</script>

</head>
<body class="dark">

	<header class="post-header">
		<div class="content">
			<h1 class="title">Title of the Post</h1>
			<ul class="links">
				<li>
					<a href="../index.html">
						<img src="./../../imgs/icons/home.svg" alt="">
					</a>
				</li>
				<li>
					<a href="https://github.com/theyordanos">
						<img src="./../../imgs/icons/github.svg" alt="">
					</a>
				</li>
				<li class="theme-toggle">
					<img src="./../../imgs/icons/sun.svg" class="sun">
					<img src="./../../imgs/icons/moon.svg" class="moon">
				</li>
			</ul>
		</div>
	</header>

	<article class="post-article">
`

post_footer: string = `
	</article>

	<script src="./../../scripts/toggle.js"></script>

</body>
</html>
`

main :: proc() {
	if !os.exists(default_output) do os.make_directory(default_output)
	read_and_write_markdown(default_input)
}

read_and_write_markdown :: proc(path: string) {
	assert(
		os.exists(path),
		fmt.aprintfln("%s: %s", path, "doesn't exist"))

	if os.is_dir(path) {
		// Trim input folder name from output
		output_path := fmt.aprintf("%s/%s", default_output, strings.trim(path, fmt.aprintf("%s/", default_input)))
		if !os.exists(output_path) do os.make_directory(output_path)

		input_folder, err := os2.open(path)
		assert(
			err == nil,
			fmt.aprint("Failed opening folder %v: %v", input_folder, err))

		file_info, err2 := os2.read_directory(input_folder, 0, context.allocator)
		assert(
			err2 == nil,
			fmt.aprint("Failed reading directory %v: %v", file_info, err2))

		// Read every file
		for file in file_info {
			read_and_write_markdown(file.fullpath)
		}
	} else {
		// Copy every file to output folder if it isn't markdown
		if !strings.has_suffix(path, ".md") {
			name := strings.trim(path, fmt.aprintf("%s/", default_input))
			output := fmt.aprintf("%s/%s", default_output, name)

			os2.copy_file(output, path)
			return
		}

		// Convert and write md -> html
		if md_content, ok := os.read_entire_file(path); ok {
			html_content := cm.markdown_to_html_from_string(string(md_content), {})

			name := strings.trim(path, ".md")
			name = strings.trim(name, fmt.aprintf("%s/", default_input))
			output := fmt.aprintf("%s%s.%s", default_output, name, "html")

			final: string = fmt.aprintfln("%s%s%s", post_header, html_content, post_footer)
			os.write_entire_file(output, transmute([]u8)final)

			fmt.printfln("%s --> %s", path, output)
		} else {
			fmt.println("Couldn't read file:", path)
		}
	}
}
