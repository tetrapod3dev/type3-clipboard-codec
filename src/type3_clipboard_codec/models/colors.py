from dataclasses import dataclass


@dataclass(frozen=True)
class Type3Color:
    """Type3 palette color with observed CPropertyExtend raw candidate value."""
    name: str
    hex_rgb: str

    @property
    def raw_candidate(self) -> int:
        """
        Observed rectangle color fields store bytes as G, B, R, 0x00.
        The source palette is documented as RRGGBB.
        """
        hex_value = self.hex_rgb.upper()
        red = int(hex_value[0:2], 16)
        green = int(hex_value[2:4], 16)
        blue = int(hex_value[4:6], 16)
        return green | (blue << 8) | (red << 16)

    @property
    def raw_candidate_rgb0(self) -> int:
        """
        Alternate observed encoding candidate: bytes as R, G, B, 0x00
        (little-endian u32 == 0x00BBGGRR).
        """
        hex_value = self.hex_rgb.upper()
        red = int(hex_value[0:2], 16)
        green = int(hex_value[2:4], 16)
        blue = int(hex_value[4:6], 16)
        return red | (green << 8) | (blue << 16)


TYPE3_PALETTE: tuple[Type3Color, ...] = (
    Type3Color("Black", "000000"),
    Type3Color("Blue", "000080"),
    Type3Color("Green", "008000"),
    Type3Color("Cyan", "008080"),
    Type3Color("Red", "800000"),
    Type3Color("Magenta", "800080"),
    Type3Color("Brown", "808000"),
    Type3Color("Light Gray", "C0C0C0"),
    Type3Color("Gray", "808080"),
    Type3Color("Light Blue", "0000FF"),
    Type3Color("Light Green", "00FF00"),
    Type3Color("Light Cyan", "00FFFF"),
    Type3Color("Light Red", "FF0000"),
    Type3Color("Light Magenta", "FF00FF"),
    Type3Color("Yellow", "FFFF00"),
    Type3Color("White", "FFFFFF"),
    Type3Color("Purple", "B216E6"),
    Type3Color("Orange", "FF6400"),
    Type3Color("Pink", "FF98CC"),
    Type3Color("Dark Brown", "B27E7E"),
    Type3Color("Powder Blue", "CCCCFF"),
    Type3Color("Pastel Blue", "9898FF"),
    Type3Color("Baby Blue", "6498FF"),
    Type3Color("Electric Blue", "6464FF"),
    Type3Color("Twilight Blue", "7E7EE6"),
    Type3Color("Navy Blue", "3060CC"),
    Type3Color("Deep Navy Blue", "4A4AB2"),
    Type3Color("Desert Blue", "6498CC"),
    Type3Color("Sky Blue", "00CCFF"),
    Type3Color("Ice Blue", "98FFFF"),
    Type3Color("Light BlueGreen", "B2E6E6"),
    Type3Color("Ocean Green", "98CCCC"),
    Type3Color("Moss Green", "7EB2B2"),
    Type3Color("Dark Green", "649898"),
    Type3Color("Forest Green", "4AB27E"),
    Type3Color("Grass Green", "30CC64"),
    Type3Color("Kentucky Green", "64CC98"),
    Type3Color("Light Green", "4AE67E"),
    Type3Color("Spring Green", "4AE64A"),
    Type3Color("Turquoise", "64FFCC"),
    Type3Color("Sea Green", "4AE6B2"),
    Type3Color("Faded Green", "B2E6B2"),
    Type3Color("Ghost Green", "CCFFCC"),
    Type3Color("Mint Green", "98FF98"),
    Type3Color("Army Green", "98CC98"),
    Type3Color("Avocado Green", "98CC64"),
    Type3Color("Martian Green", "B2E64A"),
    Type3Color("Dull Green", "B2E67E"),
    Type3Color("Chartreuse", "98FF00"),
    Type3Color("Moon Green", "CCFF64"),
    Type3Color("Murky Green", "989864"),
    Type3Color("Olive Drab", "B2B27E"),
    Type3Color("Khaki", "CCCC98"),
    Type3Color("Olive", "CCCC64"),
    Type3Color("Banana Yellow", "E6E64A"),
    Type3Color("Light Yellow", "FFFF64"),
    Type3Color("Chalk", "FFFF98"),
    Type3Color("Pale Yellow", "FFFFCC"),
    Type3Color("Red Brown", "E67E4A"),
    Type3Color("Gold", "E6B24A"),
    Type3Color("Autumn Orange", "FF6430"),
    Type3Color("Light Orange", "FF9830"),
    Type3Color("Peach", "FF9864"),
    Type3Color("Deep Yellow", "FFCC00"),
    Type3Color("Sand", "FFCC98"),
    Type3Color("Walnut", "B27E4A"),
    Type3Color("Ruby Red", "CC3030"),
    Type3Color("Brick Red", "E64A16"),
    Type3Color("Tropical Pink", "FF6464"),
    Type3Color("Soft Pink", "FF9898"),
    Type3Color("Faded Pink", "FFCCCC"),
    Type3Color("Crimson", "CC6498"),
    Type3Color("Regal Red", "E64A7E"),
    Type3Color("Deep Rose", "E64AB2"),
    Type3Color("Neon Red", "FF0064"),
    Type3Color("Deep Pink", "FF6498"),
    Type3Color("Hot Pink", "FF3098"),
    Type3Color("Dusty Rose", "E67EB2"),
    Type3Color("Plum", "B24AB2"),
    Type3Color("Deep Violet", "CC30CC"),
    Type3Color("Light Violet", "FF98FF"),
    Type3Color("Violet", "E67EE6"),
    Type3Color("Dusty Plum", "CC98CC"),
    Type3Color("Pale Purple", "E6B2E6"),
    Type3Color("Majestic Purp", "B24AE6"),
    Type3Color("Neon Purple", "CC30FF"),
    Type3Color("Light Purple", "CC64FF"),
    Type3Color("Twilight Viol", "B27EE6"),
    Type3Color("Easter Purple", "CC98FF"),
    Type3Color("Deep Purple", "7E4AB2"),
    Type3Color("Grape", "9864CC"),
    Type3Color("Blue Violet", "9864FF"),
    Type3Color("Blue Purple", "9800FF"),
    Type3Color("Deep River", "7E16E6"),
    Type3Color("Deep Azure", "6430FF"),
    Type3Color("Storm Blue", "6430CC"),
    Type3Color("Deep Blue", "4A16E6"),
    Type3Color("100% Black", "000000"),
    Type3Color("90% Black", "8C8C8C"),
    Type3Color("80% Black", "989898"),
    Type3Color("70% Black", "A6A6A6"),
    Type3Color("60% Black", "B2B2B2"),
    Type3Color("50% Black", "C0C0C0"),
    Type3Color("40% Black", "CCCCCC"),
    Type3Color("30% Black", "D8D8D8"),
    Type3Color("20% Black", "E6E6E6"),
    Type3Color("10% Black", "F2F2F2"),
)


TYPE3_COLORS_BY_RAW: dict[int, Type3Color] = {}
for color in TYPE3_PALETTE:
    TYPE3_COLORS_BY_RAW.setdefault(color.raw_candidate, color)

TYPE3_COLORS_BY_RGB0_RAW: dict[int, Type3Color] = {}
for color in TYPE3_PALETTE:
    TYPE3_COLORS_BY_RGB0_RAW.setdefault(color.raw_candidate_rgb0, color)
