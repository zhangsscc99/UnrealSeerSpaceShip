#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SeerAnchorNius.generated.h"

class APlayerController;
class SSeerCommsPanel;
class UPointLightComponent;
class UStaticMeshComponent;
class UTexture2D;

/**
 * 主播纽斯 — the floating broadcaster robot standing in front of the corridor's
 * far bulkhead. Hovers, turns to face the player, and opens the holographic
 * comms console when 赛尔 walks into range.
 */
UCLASS()
class UNREALSEERSPACESHIP_API ASeerAnchorNius : public AActor
{
	GENERATED_BODY()

public:
	ASeerAnchorNius();
	virtual void Tick(float DeltaSeconds) override;

	/** Player must get this close for the dialogue to open. */
	UPROPERTY(EditAnywhere, Category = "Seer|Interaction")
	float TriggerRadius = 620.f;

	/** Walking further away than this closes the panel. */
	UPROPERTY(EditAnywhere, Category = "Seer|Interaction")
	float ReleaseRadius = 900.f;

	UPROPERTY(EditAnywhere, Category = "Seer|Hover")
	float HoverAmplitude = 9.f;

	UPROPERTY(EditAnywhere, Category = "Seer|Hover")
	float HoverSpeed = 1.45f;

	/** When true and TravelLevelName resolves to a cooked map, the route button travels there. */
	UPROPERTY(EditAnywhere, Category = "Seer|Travel")
	bool bAllowTravel = true;

	UPROPERTY(EditAnywhere, Category = "Seer|Travel")
	FName TravelLevelName = TEXT("Kros");

	// --- dialogue copy (editable per placed instance) ----------------------
	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue")
	FText SpeakerName;

	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue")
	FText SpeakerTag;

	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue", meta = (MultiLine = true))
	FText DialogueText;

	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue")
	FText DestinationName;

	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue")
	FText DestinationMeta;

	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue")
	FText CtaLabel;

	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue")
	FText UnavailableStatus;

	UPROPERTY(EditAnywhere, Category = "Seer|Dialogue")
	TObjectPtr<UTexture2D> PortraitTexture;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void OpenPanel();
	void HandleTravelConfirmed();
	void HandlePanelClosed();
	void RestorePlayerInput();

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UPointLightComponent> KeyLight;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UPointLightComponent> RimLight;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UPointLightComponent> FillLight;

	TSharedPtr<SSeerCommsPanel> Panel;
	TWeakObjectPtr<APlayerController> CachedPC;

	float HoverTime = 0.f;
	float CurrentYaw = 180.f;
	float IdleYaw = 180.f;
	bool bPanelOpen = false;
	/** Set after a manual close so the panel does not instantly reopen while the player stands still. */
	bool bCooldown = false;
};
