#include "SeerCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "UObject/ConstructorHelpers.h"

ASeerCharacter::ASeerCharacter()
{
	PrimaryActorTick.bCanEverTick = false;

	UCapsuleComponent* Capsule = GetCapsuleComponent();
	Capsule->InitCapsuleSize(34.f, 88.f);

	// Walk, do not fly: gravity plus the floor keeps the character on the ground.
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = 520.f;
	Move->BrakingDecelerationWalking = 2400.f;
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 640.f, 0.f);

	// Jumping: one hop from the ground, a second kick in the air.
	Move->JumpZVelocity = 620.f;
	Move->AirControl = 0.6f;
	Move->GravityScale = 1.6f;
	JumpMaxCount = 2;

	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	// The robot mesh: origin is at the feet, and the source FBX is 100x too large.
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> SeerMesh(
		TEXT("/Game/SeerLab/Characters/SK_Seer.SK_Seer"));
	if (SeerMesh.Succeeded())
	{
		GetMesh()->SetSkeletalMesh(SeerMesh.Object);
		GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -88.f));
		GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
		GetMesh()->SetRelativeScale3D(FVector(0.01739f));
	}

	// Fixed 2.5D camera: absolute location/rotation, so it ignores the pawn's transform.
	FixedCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FixedCam"));
	FixedCamera->SetupAttachment(RootComponent);
	FixedCamera->SetUsingAbsoluteLocation(true);
	FixedCamera->SetUsingAbsoluteRotation(true);
	FixedCamera->SetUsingAbsoluteScale(true);
	FixedCamera->SetRelativeLocation(FVector(0.f, -1250.f, 1150.f));
	FixedCamera->SetRelativeRotation(FRotator(-45.f, 90.f, 0.f));
	FixedCamera->FieldOfView = 90.f;
	FixedCamera->bUsePawnControlRotation = false;

	// Existing project input assets; A/D feed X and W/S feed Y through swizzle modifiers.
	static ConstructorHelpers::FObjectFinder<UInputAction> MoveAsset(
		TEXT("/Game/Input/IA_Move.IA_Move"));
	if (MoveAsset.Succeeded())
	{
		MoveAction = MoveAsset.Object;
	}

	// Constructor-time asset loading has to go through ConstructorHelpers; LoadObject
	// silently returns null while the CDO is being built.
	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextA(
		TEXT("/Game/Input/IMC_A.IMC_A"));
	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextD(
		TEXT("/Game/Input/IMC_D.IMC_D"));
	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextW(
		TEXT("/Game/Input/IMC_W.IMC_W"));
	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextS(
		TEXT("/Game/Input/IMC_S.IMC_S"));

	for (const auto& Finder : { &ContextA, &ContextD, &ContextW, &ContextS })
	{
		if (Finder->Succeeded())
		{
			MappingContexts.Add(Finder->Object);
		}
	}
}

void ASeerCharacter::BeginPlay()
{
	Super::BeginPlay();

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			for (UInputMappingContext* Context : MappingContexts)
			{
				if (Context)
				{
					Subsystem->AddMappingContext(Context, 0);
				}
			}
			UE_LOG(LogTemp, Warning, TEXT("SeerCharacter: %d mapping contexts registered, MoveAction=%s"),
				MappingContexts.Num(), MoveAction ? TEXT("yes") : TEXT("no"));
			return;
		}
	}
	UE_LOG(LogTemp, Error, TEXT("SeerCharacter: no player controller / input subsystem in BeginPlay"));
}

void ASeerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	// Enhanced Input never fires in this project (the graph nodes and the C++ binding
	// both stay silent), so movement is bound through the legacy axis path, whose
	// mappings live in Config/DefaultInput.ini.
	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ASeerCharacter::MoveForward);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ASeerCharacter::MoveRight);

	// ACharacter::Jump respects JumpMaxCount, so the same binding gives the double jump.
	PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ACharacter::Jump);
	PlayerInputComponent->BindAction(TEXT("Jump"), IE_Released, this, &ACharacter::StopJumping);
}

void ASeerCharacter::Move(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();

	// The camera looks along +Y with screen-right at -X, so map the 2D input onto that basis.
	AddMovementInput(FVector(0.f, 1.f, 0.f), Axis.Y);
	AddMovementInput(FVector(-1.f, 0.f, 0.f), Axis.X);
}

void ASeerCharacter::MoveForward(float Value)
{
	if (Value != 0.f)
	{
		AddMovementInput(FVector(0.f, 1.f, 0.f), Value);
	}
}

void ASeerCharacter::MoveRight(float Value)
{
	if (Value != 0.f)
	{
		AddMovementInput(FVector(-1.f, 0.f, 0.f), Value);
	}
}
