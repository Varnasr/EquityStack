# Simple choropleth map using GeoPandas + Folium
import geopandas as gpd
import folium

def map_district_data(shapefile_path, data, join_col='district'):
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.merge(data, on=join_col)

    m = folium.Map(location=[23.5, 78.9], zoom_start=5)
    folium.Choropleth(
        geo_data=gdf,
        data=gdf,
        columns=[join_col, 'value'],
        key_on=f'feature.properties.{join_col}',
        fill_color='YlGn',
        legend_name='District Metric'
    ).add_to(m)
    return m