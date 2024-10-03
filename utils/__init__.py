def camel_to_snake(camel_str):
    # Find all instances where a lowercase letter is followed by an uppercase letter
    # and insert an underscore between them, then convert to lowercase
    snake_str = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    if snake_str.find("f_k") >= 0:
        snake_str = snake_str.replace("f_k", "fk")
    if snake_str.find("i_k") >= 0:
        snake_str = snake_str.replace("i_k", "ik")
    return snake_str

def snake_to_camel(snake_str):
    # Split the string by underscores
    if snake_str.find("fk") > 0:
        snake_str = snake_str.replace("fk","FK")
    if snake_str.find("ik") > 0:
        snake_str = snake_str.replace("ik","IK")
    components = snake_str.split('_')
    # Capitalize the first letter of each component except the first one, and join them
    camel_case_str = components[0] + ''.join(x.title() for x in components[1:])
    return camel_case_str