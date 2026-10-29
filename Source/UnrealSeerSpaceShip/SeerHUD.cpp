#include "SeerHUD.h"

#include "Engine/Canvas.h"
#include "Engine/Texture2D.h"
#include "Engine/GameEngine.h"
#include "GameFramework/InputSettings.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// Normalized rects, origin top-left. Jump sits lower-right, the look pad is
	// middle-right and shifted up as requested.
	const FBox2D JumpRectNorm(FVector2D(0.76, 0.58), FVector2D(0.94, 0.88));
	const FBox2D LookRectNorm(FVector2D(0.62, 0.10), FVector2D(0.98, 0.46));

	bool TouchUIVisible()
	{
		const FString Platform = UGameplayStatics::GetPlatformName();
		return Platform.StartsWith(TEXT("Android")) || Platform.StartsWith(TEXT("IOS"))
			|| GetDefault<UInputSettings>()->bAlwaysShowTouchInterface;
	}

	UTexture2D* PadTexture()
	{
		static TWeakObjectPtr<UTexture2D> Tex;
		if (!Tex.IsValid())
		{
			Tex = LoadObject<UTexture2D>(nullptr,
				TEXT("/Engine/MobileResources/HUD/VirtualJoystick_Background.VirtualJoystick_Background"));
		}
		return Tex.Get();
	}

	void DrawPad(UCanvas* Canvas, const FBox2D& Rect, const TCHAR* Label)
	{
		if (UTexture2D* Tex = PadTexture())
		{
			const FVector2D Size = Rect.GetSize();
			Canvas->SetDrawColor(FColor(100, 240, 255, 90));
			Canvas->DrawTile(Tex,
				static_cast<float>(Rect.Min.X), static_cast<float>(Rect.Min.Y),
				static_cast<float>(Size.X), static_cast<float>(Size.Y),
				0.f, 0.f, static_cast<float>(Tex->GetSizeX()), static_cast<float>(Tex->GetSizeY()),
				BLEND_Translucent);
		}
		const FVector2D TextPos = Rect.GetCenter() - FVector2D(24.f, 8.f);
		Canvas->SetDrawColor(FColor(100, 240, 255, 230));
		Canvas->DrawText(GEngine->GetMediumFont(), FText::FromString(Label),
			static_cast<float>(TextPos.X), static_cast<float>(TextPos.Y));
	}
}

FBox2D ASeerHUD::GetJumpRect(const FVector2D& ViewportSize)
{
	return FBox2D(JumpRectNorm.Min * ViewportSize, JumpRectNorm.Max * ViewportSize);
}

FBox2D ASeerHUD::GetLookRect(const FVector2D& ViewportSize)
{
	return FBox2D(LookRectNorm.Min * ViewportSize, LookRectNorm.Max * ViewportSize);
}

void ASeerHUD::DrawHUD()
{
	Super::DrawHUD();

	if (!TouchUIVisible() || !Canvas)
	{
		return;
	}

	const FVector2D ViewportSize(Canvas->SizeX, Canvas->SizeY);
	DrawPad(Canvas, GetJumpRect(ViewportSize), TEXT("JUMP"));
	DrawPad(Canvas, GetLookRect(ViewportSize), TEXT("LOOK"));
}
