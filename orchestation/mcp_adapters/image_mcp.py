def handle_images_mcp(role: str, image_urls: str):
    image_block = ""

    if role == "admin" and image_urls:
        image_block = "\n".join(
            f"- {image_url}"
            for image_url in image_urls
        )

        image_block = (
            "\n\n"
            "Images:\n"
            f"{image_block}"
        )

    return image_block