import psapi

ps_document =  psapi.LayeredFile.read("C:/Users/florianbehr/Desktop/configurator/BMW_config.psd")

layers = ps_document.layers

for layer in layers:
    if type(layer) == psapi.GroupLayer_8bit:
        print(f"Group Layer: {layer.name}")
        group_layers = layer.layers or []
        for gl in group_layers:
            print(f"Layer name: {gl.name}")

    else:
        print(f"Layer name: {layer.name}")
