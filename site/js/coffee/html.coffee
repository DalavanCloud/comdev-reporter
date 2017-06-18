
class HTML
    constructor: (type, params, children) ->
        ### create the raw element, or clone if passed an existing element ###
        if typeof type is 'object'
            @element = type.cloneNode()
        else
            @element = document.createElement(type)
        
        ### If params have been passed, set them ###
        if isHash(params)
            for key, val of params
                ### Standard string value? ###
                if typeof val is "string" or typeof val is 'number'
                    @element.setAttribute(key, val)
                else if isArray(val)
                    ### Are we passing a list of data to set? concatenate then ###
                    @element.setAttribute(key, val.join(" "))
                else if isHash(val)
                    ### Are we trying to set multiple sub elements, like a style? ###
                    for subkey,subval of val
                        if not @element[key]
                            throw "No such attribute, #{key}!"
                        @element[key][subkey] = subval
        
        ### If any children have been passed, add them to the element  ###
        if children
            ### If string, convert to textNode using txt() ###
            if typeof children is "string"
                @element.inject(txt(children))
            else
                ### If children is an array of elems, iterate and add ###
                if isArray children
                    for child in children
                        ### String? Convert via txt() then ###
                        if typeof child is "string"
                            @element.inject(txt(child))
                        else
                            ### Plain element, add normally ###
                            @element.inject(child)
                else
                    ### Just a single element, add it ###
                    @element.inject(children)
        return @element
###*
# prototype injector for HTML elements:
# Example: mydiv.inject(otherdiv)
###
HTMLElement.prototype.inject = (child) ->
    if isArray(child)
        for item in child
            # Convert to textNode if string
            if typeof item is 'string'
                item = txt(item)
            this.appendChild(item)
    else
        # Convert to textNode if string
        if typeof child is 'string'
            child = txt(child)
        this.appendChild(child)
    return child

txt = (a) ->
    return document.createTextNode(a)

