# Context-Sensitive Upgrade UI

## How It Works

The upgrade panel now appears **only when you select units**, showing only the relevant upgrades for what you've selected.

## When Upgrades Appear

### Selecting Units
- Select units by click-dragging a box around them
- Upgrade panel appears at the **bottom of the screen**
- Shows 4 unit upgrade buttons:
  - **Unit HP** - Increases unit health
  - **Unit Dmg** - Increases unit damage
  - **Unit CD** - Decreases attack cooldown (faster attacks)
  - **Unit Speed** - Increases movement speed

### Future: Selecting Castles/Resources
(Can be extended to show castle/resource upgrades when those are selected)

## UI Design

### Panel Location
- **Position**: Bottom of screen (doesn't cover the map!)
- **Width**: Expands to fit buttons horizontally
- **Background**: Semi-transparent dark overlay

### Button States
- **Green**: Can afford this upgrade
- **Dark Red**: Cannot afford (not enough resources)
- **Gray**: Maximum level reached (Lv5)

### Button Format
- Shows: `Upgrade Type Lv<current_level> ($<cost>)`
- Example: `Unit HP Lv2 ($11)`
- At max: `Unit HP LvMAX`

## How to Upgrade

1. **Select units** (click and drag to select multiple)
2. Upgrade panel appears at bottom
3. **Click upgrade buttons** to purchase
4. Green message: "Upgraded Unit HP!" (success)
5. Red message: "Not enough resources!" (failure)

## Upgrade Progression

- Costs increase: 5, 7, 11, 16, 25 resources
-Level cap: 5 levels per upgrade
- Upgrades apply to **all current and future units** of that faction

## Integration with AI

- AI still makes upgrade decisions automatically every 10 seconds
- Player gets manual control through the UI
- Both systems work together seamlessly

## Technical Notes

- Button click detection uses dynamically generated rectangles
- Buttons are only rendered (and clickable) when panel is visible
- No performance impact when nothing is selected
