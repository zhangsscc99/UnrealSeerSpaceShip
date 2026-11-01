#include "SeerGameMode.h"

#include "Engine/PlayerStartPIE.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerStart.h"
#include "SeerCharacter.h"
#include "SeerHUD.h"

DEFINE_LOG_CATEGORY_STATIC(LogSeerGameMode, Log, All);

ASeerGameMode::ASeerGameMode()
{
	DefaultPawnClass = ASeerCharacter::StaticClass();
	HUDClass = ASeerHUD::StaticClass();
}

AActor* ASeerGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
	if (!bIgnorePlayFromHereStart)
	{
		return Super::ChoosePlayerStart_Implementation(Player);
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return Super::ChoosePlayerStart_Implementation(Player);
	}

	UClass* PawnClass = GetDefaultPawnClassForController(Player);
	APawn* PawnToFit = PawnClass ? PawnClass->GetDefaultObject<APawn>() : nullptr;

	TArray<APlayerStart*> UnoccupiedStarts;
	TArray<APlayerStart*> OccupiedStarts;
	TArray<APlayerStart*> FallbackStarts;

	for (TActorIterator<APlayerStart> It(World); It; ++It)
	{
		APlayerStart* Start = *It;
		if (!IsValid(Start))
		{
			continue;
		}

		if (Start->IsA<APlayerStartPIE>())
		{
			// Created by the editor because PIE was started at the viewport camera.
			// Never let it replace the level's authored spawn point.
			UE_LOG(LogSeerGameMode, Log,
				TEXT("Ignoring PIE-only PlayerStart %s at %s; using the level's authored PlayerStart."),
				*Start->GetName(), *Start->GetActorLocation().ToCompactString());
			continue;
		}

		FallbackStarts.Add(Start);

		// FindTeleportSpot takes the location by reference and may adjust it.
		FVector Location = Start->GetActorLocation();
		FRotator Rotation = Start->GetActorRotation();
		if (!World->EncroachingBlockingGeometry(PawnToFit, Location, Rotation))
		{
			UnoccupiedStarts.Add(Start);
		}
		else if (World->FindTeleportSpot(PawnToFit, Location, Rotation))
		{
			OccupiedStarts.Add(Start);
		}
	}

	APlayerStart* ChosenStart = nullptr;
	if (UnoccupiedStarts.Num() > 0)
	{
		ChosenStart = UnoccupiedStarts[FMath::RandRange(0, UnoccupiedStarts.Num() - 1)];
	}
	else if (OccupiedStarts.Num() > 0)
	{
		ChosenStart = OccupiedStarts[FMath::RandRange(0, OccupiedStarts.Num() - 1)];
	}
	else if (FallbackStarts.Num() > 0)
	{
		// Every authored start is blocked. Use one anyway rather than let the
		// pawn spawn at the editor camera or not spawn at all.
		ChosenStart = FallbackStarts[0];
		UE_LOG(LogSeerGameMode, Warning,
			TEXT("Every authored PlayerStart is blocked; spawning at %s anyway."),
			*ChosenStart->GetName());
	}

	if (ChosenStart)
	{
		UE_LOG(LogSeerGameMode, Log, TEXT("Chose PlayerStart %s at %s."),
			*ChosenStart->GetName(), *ChosenStart->GetActorLocation().ToCompactString());
		return ChosenStart;
	}

	// No authored PlayerStart exists in this level. Keep the engine's behaviour
	// so an explicit "Play From Here" still produces a pawn instead of nothing.
	return Super::ChoosePlayerStart_Implementation(Player);
}
