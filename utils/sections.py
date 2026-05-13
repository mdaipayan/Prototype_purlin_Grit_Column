"""
Standard Structural Steel Sections as per IS 808.
Units:
- Depth (h): mm
- Flange Width (bf): mm
- Web Thickness (tw): mm
- Flange Thickness (tf): mm
- Area (Area): cm^2
- Weight (weight): kg/m
- Moment of Inertia (Ixx, Iyy): cm^4
- Elastic Section Modulus (Zxx, Zyy): cm^3
- Plastic Section Modulus (Zpx, Zpy): cm^3
"""

# Indian Standard Medium Weight Beams
ISMB = {
    "ISMB 100": {"h": 100, "bf": 50, "tw": 4.0, "tf": 7.0, "Area": 11.4, "weight": 8.9, "Ixx": 183.0, "Iyy": 12.9, "Zxx": 36.6, "Zyy": 5.16, "Zpx": 41.7, "Zpy": 8.0},
    "ISMB 150": {"h": 150, "bf": 75, "tw": 5.0, "tf": 8.0, "Area": 19.1, "weight": 15.0, "Ixx": 718.0, "Iyy": 46.8, "Zxx": 95.7, "Zyy": 12.48, "Zpx": 109.1, "Zpy": 19.3},
    "ISMB 200": {"h": 200, "bf": 100, "tw": 5.7, "tf": 10.8, "Area": 32.3, "weight": 25.4, "Ixx": 2235.0, "Iyy": 150.0, "Zxx": 223.5, "Zyy": 30.0, "Zpx": 254.8, "Zpy": 46.5},
    "ISMB 250": {"h": 250, "bf": 125, "tw": 6.9, "tf": 12.5, "Area": 47.5, "weight": 37.3, "Ixx": 5130.0, "Iyy": 334.0, "Zxx": 410.4, "Zyy": 53.44, "Zpx": 467.9, "Zpy": 82.8},
    "ISMB 300": {"h": 300, "bf": 140, "tw": 7.5, "tf": 12.4, "Area": 56.2, "weight": 44.2, "Ixx": 8603.0, "Iyy": 453.0, "Zxx": 573.5, "Zyy": 64.71, "Zpx": 653.8, "Zpy": 100.3},
    "ISMB 400": {"h": 400, "bf": 140, "tw": 8.9, "tf": 16.0, "Area": 78.4, "weight": 61.6, "Ixx": 20458.0, "Iyy": 622.0, "Zxx": 1022.9, "Zyy": 88.86, "Zpx": 1166.1, "Zpy": 137.7},
}

# Indian Standard Light Weight Beams
ISLB = {
    "ISLB 100": {"h": 100, "bf": 50, "tw": 4.0, "tf": 5.3, "Area": 10.2, "weight": 8.0, "Ixx": 165.0, "Iyy": 11.4, "Zxx": 33.0, "Zyy": 4.56, "Zpx": 37.6, "Zpy": 7.1},
    "ISLB 150": {"h": 150, "bf": 80, "tw": 4.8, "tf": 5.8, "Area": 18.0, "weight": 14.2, "Ixx": 688.0, "Iyy": 55.0, "Zxx": 91.7, "Zyy": 13.75, "Zpx": 104.6, "Zpy": 21.3},
    "ISLB 200": {"h": 200, "bf": 100, "tw": 5.4, "tf": 7.3, "Area": 25.2, "weight": 19.8, "Ixx": 1696.0, "Iyy": 115.0, "Zxx": 169.6, "Zyy": 23.0, "Zpx": 193.3, "Zpy": 35.7},
    "ISLB 250": {"h": 250, "bf": 125, "tw": 6.1, "tf": 8.2, "Area": 35.5, "weight": 27.9, "Ixx": 3717.0, "Iyy": 268.0, "Zxx": 297.4, "Zyy": 42.88, "Zpx": 339.0, "Zpy": 66.5},
}

# Indian Standard Medium Weight Channels
ISMC = {
    "ISMC 100": {"h": 100, "bf": 50, "tw": 4.7, "tf": 7.5, "Area": 11.7, "weight": 9.2, "Ixx": 192.0, "Iyy": 27.5, "Zxx": 38.4, "Zyy": 11.0, "Zpx": 43.8, "Zpy": 19.3},
    "ISMC 150": {"h": 150, "bf": 75, "tw": 5.4, "tf": 9.0, "Area": 20.8, "weight": 16.4, "Ixx": 788.0, "Iyy": 116.0, "Zxx": 105.1, "Zyy": 30.93, "Zpx": 119.8, "Zpy": 54.1},
    "ISMC 200": {"h": 200, "bf": 75, "tw": 6.1, "tf": 11.4, "Area": 28.2, "weight": 22.1, "Ixx": 1830.0, "Iyy": 153.0, "Zxx": 183.0, "Zyy": 40.8, "Zpx": 208.6, "Zpy": 71.4},
    "ISMC 250": {"h": 250, "bf": 80, "tw": 7.1, "tf": 14.1, "Area": 38.6, "weight": 30.4, "Ixx": 3880.0, "Iyy": 211.0, "Zxx": 310.4, "Zyy": 52.75, "Zpx": 353.9, "Zpy": 92.3},
    "ISMC 300": {"h": 300, "bf": 90, "tw": 7.6, "tf": 13.6, "Area": 45.6, "weight": 35.8, "Ixx": 6362.0, "Iyy": 310.0, "Zxx": 424.1, "Zyy": 68.89, "Zpx": 483.5, "Zpy": 120.6},
}

# Combine all dictionaries into one master lookup variable
ALL_SECTIONS = {}
ALL_SECTIONS.update(ISMB)
ALL_SECTIONS.update(ISLB)
ALL_SECTIONS.update(ISMC)
