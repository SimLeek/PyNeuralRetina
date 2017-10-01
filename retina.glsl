#version 330
uniform sampler2D tex;
in vec2 tex_pos;
out vec4 color;

float surround_total;
float num_total;

float layer_inhb[8];

//typedef enum {RED, GREEN, BLUE} color_rgb;

//consts, because glsl compilers are wimpy
const uint RED   = 0x00000001u;
const uint GREEN = 0x00000002u;
const uint BLUE  = 0x00000004u;

//#define SURROUND_CENTER
//    #define FALSE_COLOR
#define SWAP_MSB
//#define SHOW_LEVEL 4
#ifdef SHOW_LEVEL
    uint show_level(uint x) { return ((x)<<(SHOW_LEVEL) & uint(128))%uint(256);}
#else
    #define show_level(X) X
#endif

float get_center(vec2 pos, uint col){
    float center;

    switch(col){
        case RED:
            center = texelFetch(tex, ivec2(pos), 0).r;
            break;
        case GREEN:
            center = texelFetch(tex, ivec2(pos), 0).g;
            break;
        case BLUE:
            center = texelFetch(tex, ivec2(pos), 0).b;
            break;
    }

    return center;
}

float get_pixel_color(ivec2 pos, uint col){
    switch(col){
        case RED:
            return texelFetch(tex, pos, 0).r;
        case GREEN:
            return texelFetch(tex, pos, 0).g;
        case BLUE:
            return texelFetch(tex, pos, 0).b;
    }
    return 0.0;
}

void update_surround(vec2 pos, int radius, uint col){
    float surround_add=0.0;

    int rad=radius+1;
    int num_add=0;

    for(int i=0; i<2*rad+1; ++i){
        surround_add += get_pixel_color(ivec2(pos) + ivec2(i-rad, -rad), col);
        surround_add += get_pixel_color(ivec2(pos) + ivec2(i-rad, rad), col);
        num_add+=2;
    }
    for(int j=1; j<2*rad; ++j){
        surround_add += get_pixel_color(ivec2(pos) + ivec2(-rad, j-rad), col);
        surround_add += get_pixel_color(ivec2(pos) + ivec2(rad, j-rad), col);
        num_add+=2;
    }

    surround_total = surround_total + surround_add ;
    num_total = num_total + num_add;
}

uint center_surround(vec2 pos, int radius, uint col){
    //imagine a > in place of the _
    //use: https://gamedev.stackexchange.com/a/98065

    float center = get_center(pos, col);
    update_surround(pos, radius, col);
    float surround;

    if(col==RED){
     surround = surround_total / (num_total*layer_inhb[radius]/*<-input inhibition goes here*/);
    }else{
     surround = surround_total / (num_total*layer_inhb[radius]/*<-input inhibition goes here*/);
    }


   #ifdef SWAP_MSB
   if(center>surround){
        return uint(128)>>radius;
    }else{
        return uint(0)>>radius;
    }
   #else
    if(center>surround){
        return uint(1)<<radius;
    }else{
        return uint(0)<<radius;
    }
    #endif
}

uint surround_center(vec2 pos, int radius, uint col){
    //imagine a > in place of the _
    //use: https://gamedev.stackexchange.com/a/98065
    //todo: can use previous surround and center values to speed up

    float center = get_center(pos, col);
    update_surround(pos, radius, col);
    float surround;
    /*if(col==RED){
     surround = surround_total / (num_total-1);
    }else{
     surround = surround_total / (num_total);
    }*/
    surround = surround_total*layer_inhb[radius]/*<-input inhibition goes here*/ / (num_total);

    #ifdef SWAP_MSB
    if(surround>center){
        return uint(128)>>radius;
    }else{
        return uint(0)>>radius;
    }
    #else
    if(surround>center){
        return uint(1)<<radius;
    }else{
        return uint(0)<<radius;
    }
    #endif
}

vec2 fisheye(vec2 in_pos, float amount){
        //from: https://stackoverflow.com/a/6227310

        vec2 center_xform_vec = vec2(0.5, 0.5);
        float center_xform_vec_len = length(center_xform_vec);
        vec2 r = (in_pos - center_xform_vec);
        float r_len = length(r);
        vec2 barrel_vec = (r * (1+ amount * r_len * r_len));

        float barrel_max = (sqrt(1+(720.0/1280.0)*(720.0/1280.0)) * (1+abs(amount)*center_xform_vec_len*center_xform_vec_len));
        vec2 barrel_norm = barrel_vec/barrel_max + .5;

        return barrel_norm;
    }



vec3 rgc(vec2 coord){
    uint red=uint(0);
    uint green = uint(0);
    uint blue = uint(0);
    //todo: add input image
    //todo: add input rule: small center surrounds must be much higher than their surround compareed to larger ones
    for(int i=0; i<8; ++i){
#ifdef SURROUND_CENTER
            red = red | surround_center(coord, i, RED);
    #ifdef FALSE_COLOR
            uint red2 = (green&blue);
            red = red2;
    #endif
#else
            surround_total = 0.0;
            num_total = 0;
            red = red | center_surround(coord, i, RED);
#endif
        if (red>uint(0)){
        break;
        }
    }
    for(int i=0; i<8; ++i){
#ifdef SURROUND_CENTER
            green = green | surround_center(coord, i, GREEN);
    #ifdef FALSE_COLOR
            uint green2 = (red&blue);
            green = green2;
    #endif
#else
            surround_total = 0.0;
            num_total = 0;
            green = green | center_surround(coord, i, GREEN);
#endif
        if (green>uint(0)){
        break;
        }
    }
    for(int i=0; i<8; ++i){
#ifdef SURROUND_CENTER
            blue = blue | surround_center(coord, i, BLUE);
    #ifdef FALSE_COLOR
            uint blue2 = (red&green);
            blue = blue2;
    #endif
#else
            surround_total = 0.0;
            num_total = 0;
            blue = blue | center_surround(coord, i, BLUE);
#endif
        if (blue>uint(0)){
        break;
        }
    }
    vec3 rgc_dot;
    rgc_dot.r = (float(show_level(red)))/255;//todo: report this bug.
    rgc_dot.g = (float(show_level(green)))/255;
    rgc_dot.b = (float(show_level(blue)))/255;

    return rgc_dot;
}

void main() {
    //consider: https://stackoverflow.com/a/18454838
    surround_total = 0.0;
    num_total = 0;
    layer_inhb = float[](.5, .75, 0.875, 0.9375, 0.96875, 0.984375, 0.9921875, 1.0);

    //vec2 new_coord = fisheye(tex_pos, 2.0);

    vec3 rgc_dot = rgc(vec2(tex_pos.x*1280, tex_pos.y*720));
    //rgc_dot +=

    color = vec4( rgc_dot.bgr, 1.0);
    //color = vec4(vec3(texelFetch(tex, ivec2(tex_pos*720), 0).bgr), 1.0);
}