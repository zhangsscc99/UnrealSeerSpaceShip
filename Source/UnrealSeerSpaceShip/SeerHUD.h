#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "SeerHUD.generated.h"

/**
 * Touch HUD for the lab.
 *
 * The engine touch interface only draws the left move stick; everything on the
 * right side is handled here and in ASeerCharacter:
 *  - a dedicated Jump button (right side, lower area)
 *  - a Look pad indicator (right side, middle-upper area) marking the drag zone
 *    that orbits the camera
 *
 * The rects are defined here so the character's touch handlers and the drawing
 * code can never drift apart. Coordinates are normalized 0..1, origin top-left.
 */
UCLASS()
class UNREALSEERSPACESHIP_API ASeerHUD : public AHUD
{
	GENERATED_BODY()

public:
	static FBox2D GetJumpRect(const FVector2D& ViewportSize);
	static FBox2D GetLookRect(const FVector2D& ViewportSize);

	virtual void DrawHUD() override;
};
