package main

import "core:os"
import "core:os/os2"
import "core:fmt"
import "core:strings"
import "core:encoding/json"

import cm "vendor:commonmark"

Metadata :: struct {
	title: string,
	description: string,
	date: string,
	thumbnail: string,
	path: string
}

metadatas: [dynamic]Metadata

default_output: string = "posts"
default_input: string = "markdown"

post_header: string
post_footer: string

index_path: string = "index.html"

main :: proc() {
	// Templates
	read_templates()

	// Posts
	if !os.exists(default_output) do os.make_directory(default_output)
	read_and_write_markdown(default_input)

	// Index
	modify_index()
}

modify_index :: proc() {
	index_data, ok_i := os.read_entire_file("templates/index.txt")
	if !ok_i do fmt.println("Couldn't reading index")

	post_link_data, ok_p := os.read_entire_file("templates/post_link.txt")
	if !ok_p do fmt.println("Couldn't reading post link")

	all_posts_link: string
	#reverse for data in metadatas {
		link: string = strings.clone_from_bytes(post_link_data)

		link, _ = strings.replace(link, "{{link}}", data.path, 1)
		link, _ = strings.replace(link, "{{title}}", data.title, 1)
		link, _ = strings.replace(link, "{{description}}", data.description, 1)
		link, _ = strings.replace(link, "{{date}}", data.date, 1)

		all_posts_link = strings.join([]string{all_posts_link, link}, "\n")
	}

	index_string: string = string(index_data)
	index_string, _ = strings.replace(index_string, "{{posts}}", all_posts_link, 1)

	os.write_entire_file(index_path, transmute([]u8)index_string)
}

read_templates :: proc() {
	h_data, ok_h := os.read_entire_file("templates/post_header.txt")
	if !ok_h do fmt.println("Couldn't reading post header")
	post_header = string(h_data)

	f_data, ok_f := os.read_entire_file("templates/post_footer.txt")
	if !ok_f do fmt.println("Couldn't reading post footer")
	post_footer = string(f_data)
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
			// Extract Metadata
			it := string(md_content)
			is_first: bool = true
			metadata_json: string = ""

			for line in strings.split_lines_iterator(&it) {
				if line == "" do continue

				if line == "---" && is_first {
					is_first = false
					continue
				}

				if line == "---" && !is_first do break

				metadata_json = strings.join([]string{metadata_json, line}, "")
			}
			data: Metadata
			json.unmarshal(transmute([]u8)metadata_json, &data)

			it = strings.trim(it, metadata_json)
			md_content = transmute([]u8)it

			// Parse md to html
			html_content := cm.markdown_to_html_from_string(string(md_content), {})

			// Filen and output name
			name := strings.trim(path, ".md")
			name = strings.trim(name, fmt.aprintf("%s/", default_input))
			output := fmt.aprintf("%s%s.%s", default_output, name, "html")

			// Replace things in header
			header: string = strings.clone(post_header)
			header, _ = strings.replace_all(header, "{{title}}", data.title)

			// Write
			final: string = fmt.aprintfln("%s%s%s", header, html_content, post_footer)
			os.write_entire_file(output, transmute([]u8)final)

			data.path = output
			append(&metadatas, data)

			fmt.printfln("%s --> %s", path, output)
		} else {
			fmt.println("Couldn't read file:", path)
		}
	}
}
