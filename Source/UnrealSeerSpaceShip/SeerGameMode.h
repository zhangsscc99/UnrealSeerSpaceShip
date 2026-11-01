#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SeerGameMode.generated.h"

/**
 * GameMode for the lab: wires the Seer pawn and the touch HUD together in C++
 * so nothing depends on editing Blueprint class defaults.
 */
UCLASS()
class UNREALSEERSPACESHIP_API ASeerGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASeerGameMode();

	/**
	 * Picks one of the level's authored PlayerStarts, deliberately ignoring the
	 * transient APlayerStartPIE actor.
	 *
	 * Starting PIE from the viewport camera ("Play From Here", or an automation
	 * tool that passes StartTransform) makes the editor spawn an APlayerStartPIE
	 * at that camera. AGameModeBase::ChoosePlayerStart always prefers that actor
	 * over every real PlayerStart, so the pawn appears wherever the camera was --
	 * and if the camera is outside the level, the pawn falls into the void.
	 */
	virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;

	/**
	 * When true, PIE-only PlayerStart actors are ignored and the authored
	 * PlayerStart always wins. Turn this off to restore the engine behaviour
	 * (use "Play From Here" to spawn exactly at the editor camera).
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Seer|Spawning")
	bool bIgnorePlayFromHereStart = true;
};
