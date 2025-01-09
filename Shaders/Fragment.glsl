#version 450

in vec2 TexCoords;  
out vec4 FragColor;  

layout(binding = 0) uniform sampler2D Image;  

void main()
{
    FragColor = texture(Image, TexCoords);
}