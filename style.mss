Map {
  background-color: transparent;
}

#blockgroups {
  line-color:#333;
  line-width:5;
  line-opacity:0.5;
  polygon-opacity:0.2;
  polygon-fill:#eea;
}


#parcels[zoom>=12] {
  line-color:#666;
  line-width:1;
  polygon-opacity:0.8;
  polygon-fill:#ddd;
}

#buildings[zoom>=13] {
  line-color:#333;
  line-width:1;
  polygon-opacity:0.8;
  polygon-fill:#a9b;
}


#addresses[zoom>=16] {
  marker-width:6;
  marker-fill:#88a;
  marker-line-color:#333;
  marker-allow-overlap:true;
  marker-ignore-placement:true;
  [zoom=16] {
    marker-width:3;
  }
}
