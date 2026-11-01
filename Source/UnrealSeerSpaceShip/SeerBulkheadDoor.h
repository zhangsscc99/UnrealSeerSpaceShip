#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SeerBulkheadDoor.generated.h"

class UBoxComponent;
class USceneComponent;
class UStaticMeshComponent;

/**
 * Clean two-panel sliding bulkhead used at the corridor ends.
 *
 * The player walking into the trigger slides both panels aside. If
 * bTeleportPlayer is set, the actor travels to TeleportLevelName a moment
 * after the door is open (the corridor's start door uses this to reach the
 * lab). The far door leaves bTeleportPlayer off until a destination exists.
 */
UCLASS()
class UNREALSEERSPACESHIP_API ASeerBulkheadDoor : public AActor
{
	GENERATED_BODY()

public:
	ASeerBulkheadDoor();
	virtual void Tick(float DeltaSeconds) override;
	virtual void OnConstruction(const FTransform& Transform) override;

	/** Door opening size in cm (the corridor is scaled 3x in the map). */
	UPROPERTY(EditAnywhere, Category = "Door")
	float DoorWidth = 900.f;

	UPROPERTY(EditAnywhere, Category = "Door")
	float DoorHeight = 900.f;

	/** Travel to TeleportLevelName after the door opens. */
	UPROPERTY(EditAnywhere, Category = "Door")
	bool bTeleportPlayer = false;

	UPROPERTY(EditAnywhere, Category = "Door")
	FName TeleportLevelName = TEXT("SeerLab");

	UPROPERTY(EditAnywhere, Category = "Door")
	float OpenTime = 0.9f;

	UPROPERTY(EditAnywhere, Category = "Door")
	float TeleportDelay = 0.5f;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

private:
	void ApplyDoorLayout();

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Backdrop;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> FrameLeft;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> FrameRight;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> FrameTop;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> PanelLeft;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> PanelRight;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UBoxComponent> Trigger;

	bool bOpening = false;
	float OpenStartedAt = 0.f;
	float OpenAlpha = 0.f;
	bool bTeleportPending = false;
	float TeleportAt = 0.f;
	FVector LeftClosed = FVector::ZeroVector;
	FVector RightClosed = FVector::ZeroVector;
	FVector LeftOpen = FVector::ZeroVector;
	FVector RightOpen = FVector::ZeroVector;
};
