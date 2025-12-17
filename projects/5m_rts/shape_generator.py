"""
Visual shape generator for units based on upgrade levels.
"""
import math


def generate_unit_shape(radius, hp_level, dmg_level, cd_level, speed_level, range_level):
    """
    Generate a list of polygon points for a unit based on upgrade levels.
    
    Shape philosophy (STAYS WITHIN RADIUS - carving, not extending):
    - HP: Creates indented hexagon/octagon (defensive blocky shape)
    - DMG: Sharp triangular cuts (aggressive points)
    - CD: Rapid small indentations (fast vibration look)
    - Speed: Teardrop/diamond shape (streamlined)
    - Range: Star-like with pointed tips
    
    Returns list of (x, y) points relative to center (0, 0)
    Max radius never exceeds input radius parameter.
    """
    points = []
    segments = 32  # Base circle segments
    
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        
        # Start at full radius
        r = radius
        
        # HP upgrade: Create blocky defensive shape (reduces radius at cuts)
        if hp_level > 0:
            # Make it more octagonal/hexagonal - straight edges
            sides = 6 + hp_level  # More sides with higher level
            side_angle = (2 * math.pi) / sides
            nearest_vertex = round(angle / side_angle)
            angle_to_vertex = abs(angle - (nearest_vertex * side_angle))
            # Reduce radius between vertices (creates flat edges)
            if angle_to_vertex > side_angle * 0.3:
                r *= 0.85 - (hp_level * 0.02)  # Slight indents
        
        # Damage upgrade: Sharp triangular points (star pattern)
        if dmg_level > 0:
            spike_count = 3 + dmg_level  # More spikes with level
            spike_pattern = (i % (segments // spike_count))
            if spike_pattern == 0:
                # Point stays at max radius
                pass
            elif spike_pattern <= (segments // spike_count) // 2:
                # Carve inward toward spike
                r *= 0.6 + (dmg_level * 0.03)
        
        # Attack Speed upgrade: Small rapid indentations
        if cd_level > 0:
            indent_count = 12 + cd_level * 3
            indent_pattern = (i % (segments // indent_count))
            if indent_pattern == 0:
                r *= 0.75 - (cd_level * 0.03)  # Small cuts
        
        # Speed upgrade: Elongate/compress to create teardrop
        if speed_level > 0:
            # Create asymmetric teardrop - pointed at front, flat at back
            cos_val = math.cos(angle)
            if cos_val > 0:  # Front half (moving right)
                # Keep front relatively normal but slightly pointed
                r *= 1.0 - (cos_val * 0.15 * speed_level)
            else:  # Back half
                # Flatten/indent the back
                r *= 0.8 + (abs(cos_val) * 0.1)
        
        # Range upgrade: Star points (like classic star shape)
        if range_level > 0:
            point_count = 4 + range_level
            point_pattern = (i % (segments // point_count))
            spike_width = (segments // point_count) // 3
            
            if point_pattern == 0:
                # At the point - full radius
                pass
            elif point_pattern < spike_width or point_pattern > (segments // point_count) - spike_width:
                # Near point - gradual
                r *= 0.85
            else:
                # Between points - carved in
                r *= 0.65 - (range_level * 0.02)
        
        # Ensure we never exceed original radius
        r = min(r, radius)
        
        # Calculate point
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        points.append((x, y))
    
    return points


def get_upgrade_visual_signature(hp, dmg, cd, speed, range_lvl):
    """
    Get a visual signature string for debugging/display.
    """
    parts = []
    if hp > 0:
        parts.append(f"HP+{hp}")
    if dmg > 0:
        parts.append(f"DMG+{dmg}")
    if cd > 0:
        parts.append(f"AS+{cd}")
    if speed > 0:
        parts.append(f"SPD+{speed}")
    if range_lvl > 0:
        parts.append(f"RNG+{range_lvl}")
    
    return " | ".join(parts) if parts else "Base"
