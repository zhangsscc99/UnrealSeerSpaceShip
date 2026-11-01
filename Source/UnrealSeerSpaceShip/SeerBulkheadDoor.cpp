#include "SeerBulkheadDoor.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ASeerBulkheadDoor::ASeerBulkheadDoor()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	auto MakePart = [this](const TCHAR* Name) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(Name);
		Part->SetupAttachment(Root);
		Part->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		Part->SetCollisionProfileName(TEXT("BlockAll"));
		// Everything is movable: the door layout is applied in OnConstruction,
		// and static components cannot be re-positioned or attached to a
		// movable root.
		Part->SetMobility(EComponentMobility::Movable);
		return Part;
	};

	Backdrop = MakePart(TEXT("Backdrop"));
	FrameLeft = MakePart(TEXT("FrameLeft"));
	FrameRight = MakePart(TEXT("FrameRight"));
	FrameTop = MakePart(TEXT("FrameTop"));
	PanelLeft = MakePart(TEXT("PanelLeft"));
	PanelRight = MakePart(TEXT("PanelRight"));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> PanelMat(
		TEXT("/Game/SeerCorridor/Materials/M_CorrV2_Door.M_CorrV2_Door"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> FrameMat(
		TEXT("/Game/SeerCorridor/Materials/M_CorrV2_Teal.M_CorrV2_Teal"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> DarkMat(
		TEXT("/Game/SeerCorridor/Materials/M_CorrV2_Dark.M_CorrV2_Dark"));

	for (UStaticMeshComponent* Part : {Backdrop, FrameLeft, FrameRight, FrameTop, PanelLeft, PanelRight})
	{
		if (Cube.Succeeded())
		{
			Part->SetStaticMesh(Cube.Object);
		}
	}
	if (PanelMat.Succeeded())
	{
		PanelLeft->SetMaterial(0, PanelMat.Object);
		PanelRight->SetMaterial(0, PanelMat.Object);
	}
	if (FrameMat.Succeeded())
	{
		FrameLeft->SetMaterial(0, FrameMat.Object);
		FrameRight->SetMaterial(0, FrameMat.Object);
		FrameTop->SetMaterial(0, FrameMat.Object);
	}
	if (DarkMat.Succeeded())
	{
		Backdrop->SetMaterial(0, DarkMat.Object);
	}

	Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
	Trigger->SetupAttachment(Root);
	Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Trigger->SetGenerateOverlapEvents(true);
}

void ASeerBulkheadDoor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	ApplyDoorLayout();
}

void ASeerBulkheadDoor::BeginPlay()
{
	Super::BeginPlay();

	ApplyDoorLayout();
	Trigger->OnComponentBeginOverlap.AddDynamic(this, &ASeerBulkheadDoor::HandleBeginOverlap);
}

void ASeerBulkheadDoor::ApplyDoorLayout()
{
	const float W = DoorWidth;
	const float H = DoorHeight;
	const float PanelWidth = W * 0.5f;

	const FVector PanelScale(PanelWidth / 100.f, 0.22f, H / 100.f);
	PanelLeft->SetRelativeScale3D(PanelScale);
	PanelRight->SetRelativeScale3D(PanelScale);

	// A small static gap at the centre shows the dark recess behind, so the
	// door reads as two panels instead of a blank wall (no animated patterns).
	constexpr float CenterGap = 4.f;
	LeftClosed = FVector(-W * 0.25f - CenterGap * 0.5f, 0.f, H * 0.5f);
	RightClosed = FVector(W * 0.25f + CenterGap * 0.5f, 0.f, H * 0.5f);
	LeftOpen = FVector(-W * 0.75f - CenterGap * 0.5f, 0.f, H * 0.5f);
	RightOpen = FVector(W * 0.75f + CenterGap * 0.5f, 0.f, H * 0.5f);
	PanelLeft->SetRelativeLocation(LeftClosed);
	PanelRight->SetRelativeLocation(RightClosed);

	// Dark airlock recess behind the panels so an open door reads as a passage.
	Backdrop->SetRelativeScale3D(FVector(W / 100.f, 0.5f, H / 100.f));
	Backdrop->SetRelativeLocation(FVector(0.f, -40.f, H * 0.5f));

	constexpr float FrameDepth = 40.f;
	constexpr float FrameThickness = 50.f;
	FrameLeft->SetRelativeScale3D(FVector(FrameThickness / 100.f, FrameDepth / 100.f, (H + FrameThickness) / 100.f));
	FrameLeft->SetRelativeLocation(FVector(-(W * 0.5f + FrameThickness * 0.5f), 25.f, H * 0.5f));
	FrameRight->SetRelativeScale3D(FVector(FrameThickness / 100.f, FrameDepth / 100.f, (H + FrameThickness) / 100.f));
	FrameRight->SetRelativeLocation(FVector((W * 0.5f + FrameThickness * 0.5f), 25.f, H * 0.5f));
	FrameTop->SetRelativeScale3D(FVector((W + FrameThickness * 2.f) / 100.f, FrameDepth / 100.f, FrameThickness / 100.f));
	FrameTop->SetRelativeLocation(FVector(0.f, 25.f, H + FrameThickness * 0.5f));

	Trigger->SetBoxExtent(FVector(W * 0.5f + 150.f, 250.f, H * 0.5f + 100.f));
	Trigger->SetRelativeLocation(FVector(0.f, 350.f, H * 0.5f));
}

void ASeerBulkheadDoor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bOpening || GetWorld() == nullptr)
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();

	if (OpenAlpha < 1.f)
	{
		OpenAlpha = FMath::Clamp((Now - OpenStartedAt) / FMath::Max(0.01f, OpenTime), 0.f, 1.f);
		const float Eased = FMath::InterpEaseInOut(0.f, 1.f, OpenAlpha, 2.f);
		PanelLeft->SetRelativeLocation(FMath::Lerp(LeftClosed, LeftOpen, Eased));
		PanelRight->SetRelativeLocation(FMath::Lerp(RightClosed, RightOpen, Eased));
	}

	if (bTeleportPending && Now >= TeleportAt)
	{
		bTeleportPending = false;
		UGameplayStatics::OpenLevel(this, TeleportLevelName);
	}
}

void ASeerBulkheadDoor::HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (bOpening || OtherActor == nullptr || !OtherActor->IsA<APawn>() || GetWorld() == nullptr)
	{
		return;
	}

	bOpening = true;
	OpenStartedAt = GetWorld()->GetTimeSeconds();

	if (bTeleportPlayer)
	{
		bTeleportPending = true;
		TeleportAt = OpenStartedAt + OpenTime + TeleportDelay;
	}
}
