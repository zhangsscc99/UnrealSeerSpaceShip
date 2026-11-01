#include "SeerCommsPanel.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Texture.h"
#include "Engine/Texture2D.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "Input/Events.h"
#include "Rendering/SlateRenderTransform.h"
#include "Styling/CoreStyle.h"
#include "UnrealClient.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SConstraintCanvas.h"
#include "Widgets/SCanvas.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	// Palette sampled to sit inside the corridor's own teal light, with a single
	// warm accent reserved for the one actionable element.
	const FLinearColor Abyss   = FLinearColor::FromSRGBColor(FColor(0x03, 0x0A, 0x0C));
	const FLinearColor Hull    = FLinearColor::FromSRGBColor(FColor(0x07, 0x18, 0x1C));
	const FLinearColor Plate   = FLinearColor::FromSRGBColor(FColor(0x0C, 0x2A, 0x30));
	const FLinearColor Signal  = FLinearColor::FromSRGBColor(FColor(0x35, 0xE0, 0xE0));
	const FLinearColor Halo    = FLinearColor::FromSRGBColor(FColor(0x8F, 0xF6, 0xF2));
	const FLinearColor Bone    = FLinearColor::FromSRGBColor(FColor(0xD8, 0xFB, 0xFA));
	const FLinearColor Mist    = FLinearColor::FromSRGBColor(FColor(0x7F, 0xB9, 0xBD));
	const FLinearColor Dim     = FLinearColor::FromSRGBColor(FColor(0x5A, 0x8A, 0x8F));
	const FLinearColor Amber   = FLinearColor::FromSRGBColor(FColor(0xF4, 0xA6, 0x3C));
	const FLinearColor AmberHi = FLinearColor::FromSRGBColor(FColor(0xFF, 0xD0, 0x8A));
	const FLinearColor Ink     = FLinearColor::FromSRGBColor(FColor(0x1A, 0x0F, 0x04));
	const FLinearColor Alert   = FLinearColor::FromSRGBColor(FColor(0xE5, 0x48, 0x3C));

	FColor ToColor8(const FLinearColor& Color, float Alpha)
	{
		FColor Srgb = Color.ToFColor(true);
		Srgb.A = static_cast<uint8>(FMath::Clamp(FMath::RoundToInt(Alpha * 255.f), 0, 255));
		return Srgb;
	}

	float Hash01(int32 X, int32 Y)
	{
		uint32 H = static_cast<uint32>(X) * 374761393u + static_cast<uint32>(Y) * 668265263u;
		H = (H ^ (H >> 13)) * 1274126177u;
		return static_cast<float>((H ^ (H >> 16)) & 0xffffu) / 65535.f;
	}

	UTexture2D* MakeTexture(int32 Width, int32 Height, const TCHAR* Name, TFunctionRef<FColor(int32, int32)> Pixel)
	{
		UTexture2D* Texture = UTexture2D::CreateTransient(Width, Height, PF_B8G8R8A8, FName(Name));
		if (!Texture)
		{
			return nullptr;
		}

		Texture->SRGB = true;
		Texture->NeverStream = true;
		Texture->Filter = TF_Bilinear;
		Texture->AddressX = TA_Clamp;
		Texture->AddressY = TA_Clamp;
		Texture->LODGroup = TEXTUREGROUP_UI;

		FTexture2DMipMap& Mip = Texture->GetPlatformData()->Mips[0];
		FColor* Pixels = static_cast<FColor*>(Mip.BulkData.Lock(LOCK_READ_WRITE));
		for (int32 Y = 0; Y < Height; ++Y)
		{
			for (int32 X = 0; X < Width; ++X)
			{
				Pixels[Y * Width + X] = Pixel(X, Y);
			}
		}
		Mip.BulkData.Unlock();
		Texture->UpdateResource();
		return Texture;
	}

	UTexture2D* MakePanelTexture()
	{
		constexpr int32 W = 1800;
		constexpr int32 H = 480;
		return MakeTexture(W, H, TEXT("T_SeerCommsPanel"), [](int32 X, int32 Y) -> FColor
		{
			const float Cut = 14.f;
			const float Fx = X + 0.5f;
			const float Fy = Y + 0.5f;
			const float Wf = static_cast<float>(W);
			const float Hf = static_cast<float>(H);

			const float DRect = FMath::Min(FMath::Min(Fx, Wf - Fx), FMath::Min(Fy, Hf - Fy));
			const float DTL = (Fx + Fy - Cut) * 0.70710678f;
			const float DTR = ((Wf - Fx) + Fy - Cut) * 0.70710678f;
			const float DBL = (Fx + (Hf - Fy) - Cut) * 0.70710678f;
			const float DBR = ((Wf - Fx) + (Hf - Fy) - Cut) * 0.70710678f;
			const float Edge = FMath::Min(DRect, FMath::Min(FMath::Min(DTL, DTR), FMath::Min(DBL, DBR)));
			const float Coverage = FMath::Clamp(Edge + 0.5f, 0.f, 1.f);
			if (Coverage <= 0.f)
			{
				return FColor(0, 0, 0, 0);
			}

			const float Ty = Fy / Hf;
			FLinearColor Fill = FMath::Lerp(FLinearColor(0.036f, 0.088f, 0.112f), FLinearColor(0.010f, 0.026f, 0.036f), Ty);

			// Soft centre lift so the glass feels lit from inside.
			const float Cx = (Fx / Wf - 0.5f) * 2.f;
			const float Cy = (Fy / Hf - 0.42f) * 2.f;
			const float Radial = FMath::Clamp(1.f - FMath::Sqrt(Cx * Cx + Cy * Cy), 0.f, 1.f);
			Fill += FLinearColor(0.006f, 0.030f, 0.036f) * Radial;

			// Hairline grid.
			if ((X % 48) == 0 || (Y % 48) == 0)
			{
				Fill = FMath::Lerp(Fill, Signal, 0.018f);
			}

			// Fine grain kills banding on the gradient.
			const float Grain = (Hash01(X, Y) - 0.5f) * 0.010f;
			Fill.R = FMath::Max(0.f, Fill.R + Grain);
			Fill.G = FMath::Max(0.f, Fill.G + Grain);
			Fill.B = FMath::Max(0.f, Fill.B + Grain);

			FLinearColor Out = Fill;
			float Alpha = 0.90f * Coverage;

			if (Edge < 1.4f)
			{
				Out = FMath::Lerp(Fill, Signal, 0.70f);
				Alpha = 0.96f * Coverage;
			}
			else if (Edge > 6.f && Edge < 7.f)
			{
				Out = FMath::Lerp(Fill, Signal, 0.16f);
			}

			if (Fy < 2.f)
			{
				Out = FMath::Lerp(Out, Halo, 0.22f);
			}

			// Rail rules and the column divider, baked so they stay perfectly crisp.
			auto Rule = [&](float LineY, float X0, float X1, float A)
			{
				if (FMath::Abs(Fy - LineY) < 0.75f && Fx > X0 && Fx < X1)
				{
					Out = FMath::Lerp(Out, Signal, A);
				}
			};
			Rule(54.f, 24.f, Wf - 24.f, 0.26f);
			Rule(444.f, 24.f, Wf - 24.f, 0.20f);

			// HUD corner brackets.
			auto Bracket = [&](float Bx, float By, float Dx, float Dy)
			{
				const bool bHorizontal = FMath::Abs(Fy - By) < 1.f && (Fx - Bx) * Dx >= 0.f && (Fx - Bx) * Dx < 22.f;
				const bool bVertical = FMath::Abs(Fx - Bx) < 1.f && (Fy - By) * Dy >= 0.f && (Fy - By) * Dy < 22.f;
				if (bHorizontal || bVertical)
				{
					Out = FMath::Lerp(Out, Signal, 0.55f);
				}
			};
			const float Inset = 14.f;
			Bracket(Inset, Inset, 1.f, 1.f);
			Bracket(Wf - Inset, Inset, -1.f, 1.f);
			Bracket(Inset, Hf - Inset, 1.f, -1.f);
			Bracket(Wf - Inset, Hf - Inset, -1.f, -1.f);

			return ToColor8(Out, Alpha);
		});
	}

	UTexture2D* MakeCardTexture(bool bHover)
	{
		constexpr int32 W = 1210;
		constexpr int32 H = 130;
		return MakeTexture(W, H, bHover ? TEXT("T_SeerCardHover") : TEXT("T_SeerCard"), [bHover](int32 X, int32 Y) -> FColor
		{
			const float Cut = 10.f;
			const float Fx = X + 0.5f;
			const float Fy = Y + 0.5f;
			const float Wf = static_cast<float>(W);
			const float Hf = static_cast<float>(H);

			const float DRect = FMath::Min(FMath::Min(Fx, Wf - Fx), FMath::Min(Fy, Hf - Fy));
			const float D1 = (Fx + Fy - Cut) * 0.70710678f;
			const float D2 = ((Wf - Fx) + Fy - Cut) * 0.70710678f;
			const float D3 = (Fx + (Hf - Fy) - Cut) * 0.70710678f;
			const float D4 = ((Wf - Fx) + (Hf - Fy) - Cut) * 0.70710678f;
			const float Edge = FMath::Min(DRect, FMath::Min(FMath::Min(D1, D2), FMath::Min(D3, D4)));
			const float Coverage = FMath::Clamp(Edge + 0.5f, 0.f, 1.f);
			if (Coverage <= 0.f)
			{
				return FColor(0, 0, 0, 0);
			}

			const float Ty = Fy / Hf;
			FLinearColor Fill = FMath::Lerp(Hull, Plate, 0.55f * (1.f - Ty));
			if (Fy < 1.5f)
			{
				Fill = FMath::Lerp(Fill, Halo, 0.14f);
			}

			const FLinearColor Border = bHover ? Amber : Signal;
			FLinearColor Out = Fill;
			float Alpha = (bHover ? 0.72f : 0.58f) * Coverage;

			if (Edge < 1.2f)
			{
				Out = FMath::Lerp(Fill, Border, bHover ? 0.85f : 0.55f);
				Alpha = (bHover ? 0.95f : 0.75f) * Coverage;
			}
			if (Fx < 4.f)
			{
				Out = FMath::Lerp(Out, Border, 0.90f);
				Alpha = 0.98f * Coverage;
			}

			return ToColor8(Out, Alpha);
		});
	}

	UTexture2D* MakeGlowTexture()
	{
		constexpr int32 Size = 256;
		constexpr float Half = Size * 0.5f;
		return MakeTexture(Size, Size, TEXT("T_SeerGlow"), [](int32 X, int32 Y) -> FColor
		{
			const float Dx = (X + 0.5f - Half) / Half;
			const float Dy = (Y + 0.5f - Half) / Half;
			const float R = FMath::Sqrt(Dx * Dx + Dy * Dy);
			const float A = FMath::Pow(FMath::Clamp(1.f - R, 0.f, 1.f), 2.2f);
			return FColor(255, 255, 255, static_cast<uint8>(A * 255.f));
		});
	}

	UTexture2D* MakeRingTexture(bool bDashed)
	{
		constexpr int32 Size = 512;
		constexpr float Center = Size * 0.5f;
		return MakeTexture(Size, Size, bDashed ? TEXT("T_SeerRingDash") : TEXT("T_SeerRing"), [bDashed](int32 X, int32 Y) -> FColor
		{
			const float Px = X + 0.5f - Center;
			const float Py = Y + 0.5f - Center;
			const float Dist = FMath::Sqrt(Px * Px + Py * Py);
			float A = 0.f;

			if (bDashed)
			{
				const float Deg = FMath::Fmod(FMath::Atan2(Py, Px) * (180.f / PI) + 360.f, 90.f);
				if (Deg > 8.f && Deg < 72.f)
				{
					A = FMath::Clamp(1.2f - FMath::Abs(Dist - 252.f) + 0.5f, 0.f, 1.f) * 0.65f;
				}
			}
			else
			{
				A = FMath::Clamp(1.f - FMath::Abs(Dist - 240.f) + 0.5f, 0.f, 1.f) * 0.85f;
				if (Dist > 200.f && Dist < 231.f)
				{
					const float Slot = (FMath::Atan2(Py, Px) / (2.f * PI) + 1.f) * 72.f;
					const float Nearest = FMath::RoundToFloat(Slot);
					const float PixelGap = FMath::Abs(Slot - Nearest) * (2.f * PI / 72.f) * Dist;
					const float Inner = (FMath::Fmod(Nearest, 6.f) < 0.5f) ? 202.f : 214.f;
					if (PixelGap < 0.9f && Dist > Inner && Dist < 230.f)
					{
						A = FMath::Max(A, 0.70f);
					}
				}
			}

			return FColor(255, 255, 255, static_cast<uint8>(FMath::Clamp(A, 0.f, 1.f) * 255.f));
		});
	}

	UTexture2D* MakeScanTexture()
	{
		constexpr int32 W = 4;
		constexpr int32 H = 4;
		return MakeTexture(W, H, TEXT("T_SeerScan"), [](int32 X, int32 Y) -> FColor
		{
			return (Y == 0) ? FColor(0, 0, 0, 22) : FColor(0, 0, 0, 0);
		});
	}

	UTexture2D* MakeSweepTexture()
	{
		constexpr int32 W = 256;
		constexpr int32 H = 40;
		return MakeTexture(W, H, TEXT("T_SeerSweep"), [](int32 X, int32 Y) -> FColor
		{
			const float T = (Y + 0.5f) / static_cast<float>(H);
			const float A = FMath::Pow(FMath::Sin(T * PI), 2.4f) * 0.55f;
			return ToColor8(Signal, A);
		});
	}

	UTexture2D* MakeTextScrimTexture()
	{
		constexpr int32 W = 256;
		constexpr int32 H = 64;
		return MakeTexture(W, H, TEXT("T_SeerTextScrim"), [](int32 X, int32 Y) -> FColor
		{
			const float Tx = (X + 0.5f) / static_cast<float>(W);
			const float Ty = (Y + 0.5f) / static_cast<float>(H);
			const float A = FMath::Pow(1.f - Tx, 1.45f) * 0.86f;
			const FLinearColor C = FMath::Lerp(Hull, Abyss, Ty * 0.35f);
			return ToColor8(C, A);
		});
	}

	/** Bottom-weighted scrim: transparent at the top so the game stays visible, dark behind the console. */
	UTexture2D* MakeBottomScrimTexture()
	{
		constexpr int32 W = 256;
		constexpr int32 H = 256;
		return MakeTexture(W, H, TEXT("T_SeerBottomScrim"), [](int32 X, int32 Y) -> FColor
		{
			const float T = (Y + 0.5f) / static_cast<float>(H);
			const float Alpha = FMath::SmoothStep(0.16f, 0.86f, T) * 0.88f;
			return ToColor8(Abyss, Alpha);
		});
	}

	UTexture2D* MakePillTexture()
	{
		constexpr int32 W = 340;
		constexpr int32 H = 76;
		constexpr float Radius = 10.f;
		return MakeTexture(W, H, TEXT("T_SeerPill"), [](int32 X, int32 Y) -> FColor
		{
			const float Fx = X + 0.5f - W * 0.5f;
			const float Fy = Y + 0.5f - H * 0.5f;
			const float Qx = FMath::Abs(Fx) - (W * 0.5f - Radius);
			const float Qy = FMath::Abs(Fy) - (H * 0.5f - Radius);
			const float Dist = FMath::Sqrt(FMath::Max(Qx, 0.f) * FMath::Max(Qx, 0.f) + FMath::Max(Qy, 0.f) * FMath::Max(Qy, 0.f))
				+ FMath::Min(FMath::Max(Qx, Qy), 0.f) - Radius;
			const float Coverage = FMath::Clamp(-Dist + 0.5f, 0.f, 1.f);
			if (Coverage <= 0.f)
			{
				return FColor(0, 0, 0, 0);
			}

			const float Ty = (Y + 0.5f) / static_cast<float>(H);
			FLinearColor Fill = FMath::Lerp(AmberHi, Amber, Ty);
			if ((Y + 0.5f) < 1.5f)
			{
				Fill = FMath::Lerp(Fill, FLinearColor::White, 0.35f);
			}
			return ToColor8(Fill, Coverage);
		});
	}

	UTexture2D* MakePlanetTexture()
	{
		constexpr int32 Size = 128;
		return MakeTexture(Size, Size, TEXT("T_SeerPlanet"), [](int32 X, int32 Y) -> FColor
		{
			const float Px = X + 0.5f - 64.f;
			const float Py = Y + 0.5f - 64.f;
			const float Sphere = 44.f;
			const float R2 = (Px * Px + Py * Py) / (Sphere * Sphere);
			const float R = FMath::Sqrt(R2);
			float Alpha = 0.f;
			FLinearColor Color = FLinearColor::Black;

			if (R2 < 1.f)
			{
				const float Nz = FMath::Sqrt(FMath::Max(0.f, 1.f - R2));
				const float Nx = Px / Sphere;
				const float Ny = Py / Sphere;
				const float Light = FMath::Clamp(0.20f + 0.95f * FMath::Clamp(-Nx * 0.42f - Ny * 0.52f + Nz * 0.72f, 0.f, 1.f), 0.f, 1.f);
				Color = FMath::Lerp(FLinearColor(0.012f, 0.085f, 0.070f), FLinearColor(0.28f, 0.92f, 0.66f), Light * Light);
				Color = FMath::Lerp(Color, Amber, FMath::Clamp((R - 0.82f) * 2.6f, 0.f, 1.f) * 0.22f);
				Alpha = FMath::Clamp((1.f - R) * Sphere + 0.5f, 0.f, 1.f);
			}

			// Tilted orbit ring.
			const float Theta = -18.f * (PI / 180.f);
			const float Ex = Px * FMath::Cos(Theta) + Py * FMath::Sin(Theta);
			const float Ey = -Px * FMath::Sin(Theta) + Py * FMath::Cos(Theta);
			const float RingR = FMath::Sqrt((Ex / 58.f) * (Ex / 58.f) + (Ey / 15.f) * (Ey / 15.f));
			const float RingD = FMath::Abs(RingR - 1.f) * 15.f;
			if (RingD < 1.6f)
			{
				const float RingA = FMath::Clamp(1.6f - RingD, 0.f, 1.f) * 0.75f;
				Color = FMath::Lerp(Color, Signal, RingA);
				Alpha = FMath::Max(Alpha, RingA);
			}

			// A small moon riding the ring.
			const float MoonDx = Px - 54.f;
			const float MoonDy = Py + 6.f;
			const float Moon = 3.2f - FMath::Sqrt(MoonDx * MoonDx + MoonDy * MoonDy);
			if (Moon > -0.5f)
			{
				Color = FMath::Lerp(Color, AmberHi, FMath::Clamp(Moon + 0.5f, 0.f, 1.f));
				Alpha = FMath::Max(Alpha, FMath::Clamp(Moon + 0.5f, 0.f, 1.f));
			}

			return ToColor8(Color, Alpha);
		});
	}
}

/** Keyboard pre-processor: Enter/Esc work even if the virtual joystick steals Slate focus. */
class FSeerDialogInputProcessor : public IInputProcessor
{
public:
	TWeakPtr<SSeerCommsPanel> Panel;

	virtual void Tick(const float DeltaTime, FSlateApplication& SlateApp, TSharedRef<ICursor> Cursor) override {}

	virtual bool HandleKeyDownEvent(FSlateApplication& SlateApp, const FKeyEvent& InKeyEvent) override
	{
		TSharedPtr<SSeerCommsPanel> Pinned = Panel.Pin();
		return Pinned.IsValid() && Pinned->HandleDialogKey(InKeyEvent.GetKey());
	}
};

void SSeerCommsPanel::Construct(const FArguments& InArgs)
{
	SpeakerName = InArgs._SpeakerName;
	SpeakerTag = InArgs._SpeakerTag;
	DialogueText = InArgs._DialogueText;
	DestinationName = InArgs._DestinationName;
	DestinationMeta = InArgs._DestinationMeta;
	CtaLabel = InArgs._CtaLabel;
	UnavailableStatus = InArgs._UnavailableStatus;
	PortraitTexture = InArgs._PortraitTexture;
	OnTravelConfirmed = InArgs._OnTravelConfirmed;
	OnClosed = InArgs._OnClosed;

	NameFont = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 34.f, FFontOutlineSettings(1, FLinearColor(0.f, 0.f, 0.f, 0.55f)));
	TitleFont = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 30.f, FFontOutlineSettings(1, FLinearColor(0.f, 0.f, 0.f, 0.5f)));
	BodyFont = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 24.f, FFontOutlineSettings(1, FLinearColor(0.f, 0.f, 0.f, 0.5f)));
	CtaFont = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 24.f);
	SmallFont = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 12.f);
	SmallFont.LetterSpacing = 1;
	MetaFont = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 11.f);
	TinyFont = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 10.f);
	TinyFont.LetterSpacing = 2;

	PanelTexture.Reset(MakePanelTexture());
	ScrimTexture.Reset(MakeBottomScrimTexture());
	CardTexture.Reset(MakeCardTexture(false));
	CardHoverTexture.Reset(MakeCardTexture(true));
	GlowTexture.Reset(MakeGlowTexture());
	RingTexture.Reset(MakeRingTexture(false));
	RingDashTexture.Reset(MakeRingTexture(true));
	ScanTexture.Reset(MakeScanTexture());
	SweepTexture.Reset(MakeSweepTexture());
	TextScrimTexture.Reset(MakeTextScrimTexture());
	PillTexture.Reset(MakePillTexture());
	PlanetTexture.Reset(MakePlanetTexture());
	PortraitTextureRef.Reset(LoadPortrait());

	auto ImageBrush = [](UTexture2D* Texture, FSlateBrush& Brush)
	{
		if (Texture)
		{
			Brush.SetResourceObject(Texture);
			Brush.SetImageSize(FVector2D(Texture->GetSizeX(), Texture->GetSizeY()));
		}
		Brush.DrawAs = ESlateBrushDrawType::Image;
	};

	ImageBrush(PanelTexture.Get(), PanelBrush);
	ImageBrush(ScrimTexture.Get(), ScrimBrush);
	ImageBrush(CardTexture.Get(), CardBrush);
	ImageBrush(CardHoverTexture.Get(), CardHoverBrush);
	ImageBrush(GlowTexture.Get(), GlowBrush);
	ImageBrush(RingTexture.Get(), RingBrush);
	ImageBrush(RingDashTexture.Get(), RingDashBrush);
	ImageBrush(ScanTexture.Get(), ScanBrush);
	ScanBrush.Tiling = ESlateBrushTileType::Both;
	ScanBrush.SetImageSize(FVector2D(4.f, 4.f));
	ImageBrush(SweepTexture.Get(), SweepBrush);
	ImageBrush(TextScrimTexture.Get(), TextScrimBrush);
	ImageBrush(PillTexture.Get(), PillBrush);
	ImageBrush(PlanetTexture.Get(), PlanetBrush);
	ImageBrush(PortraitTextureRef.Get(), PortraitBrush);
	TransparentBrush.DrawAs = ESlateBrushDrawType::NoDrawType;

	RouteStyle.SetNormal(CardBrush);
	RouteStyle.SetHovered(CardHoverBrush);
	RouteStyle.SetPressed(CardHoverBrush);
	RouteStyle.SetNormalPadding(FMargin(0.f));
	RouteStyle.SetPressedPadding(FMargin(0.f));

	CloseStyle.SetNormal(TransparentBrush);
	CloseStyle.SetHovered(TransparentBrush);
	CloseStyle.SetPressed(TransparentBrush);
	CloseStyle.SetNormalPadding(FMargin(0.f));
	CloseStyle.SetPressedPadding(FMargin(0.f));

	const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));

	SignalBars.SetNum(5);
	WaveBars.SetNum(16);
	IdleRules.SetNum(0);
	IdleTexts.SetNum(1);

	// ---------------------------------------------------------------------
	// Layout. Everything is authored on a 1920x1080 design canvas and scaled
	// to fit, so the composition survives phones, tablets and desktop.
	// ---------------------------------------------------------------------
	ChildSlot
	[
		SNew(SOverlay)

		// Bottom-weighted scrim: the upper half of the screen stays clear so the
		// corridor and the robot remain visible while the console is open.
		+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
		[
			SAssignNew(ScrimWidget, SImage)
			.Image(&ScrimBrush)
			.Visibility(EVisibility::Visible)
		]

		// Soft teal haze rising from the console.
		+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom)
		[
			SNew(SBox).WidthOverride(1700.f).HeightOverride(760.f)
			[
				SNew(SImage)
				.Image(&GlowBrush)
				.ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.11f))
				.Visibility(EVisibility::SelfHitTestInvisible)
			]
		]

		// Design canvas, anchored to the bottom edge of the viewport.
		+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Bottom)
		[
			SNew(SConstraintCanvas)
			+ SConstraintCanvas::Slot()
				.Anchors(FAnchors(0.5f, 1.0f, 0.5f, 1.0f))
				.Alignment(FVector2D(0.5f, 1.0f))
				.AutoSize(true)
				.Offset(FMargin(0.f))
			[
				SAssignNew(ContentRoot, SBox)
				.WidthOverride(1920.f)
				.HeightOverride(1080.f)
				[
					SNew(SCanvas)

					// Console glass: a wide bottom band, not a full-screen card.
					+ SCanvas::Slot().Position(FVector2D(60.f, 576.f)).Size(FVector2D(1800.f, 480.f))
					[
						SNew(SImage).Image(&PanelBrush).Visibility(EVisibility::SelfHitTestInvisible)
					]

					// CRT scanlines.
					+ SCanvas::Slot().Position(FVector2D(60.f, 576.f)).Size(FVector2D(1800.f, 480.f))
					[
						SNew(SImage).Image(&ScanBrush).ColorAndOpacity(FLinearColor(1.f, 1.f, 1.f, 0.40f))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Travelling scan sweep.
					+ SCanvas::Slot().Position(FVector2D(60.f, 576.f)).Size(FVector2D(1800.f, 48.f))
					[
						SAssignNew(SweepImage, SImage).Image(&SweepBrush)
						.ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.55f))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Header: LIVE + title + channel.
					+ SCanvas::Slot().Position(FVector2D(84.f, 600.f)).Size(FVector2D(10.f, 10.f))
					[
						SAssignNew(LiveDot, SImage).Image(&GlowBrush).ColorAndOpacity(Alert)
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(104.f, 590.f)).Size(FVector2D(400.f, 28.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("星际通讯")))
						.Font(CtaFont).ColorAndOpacity(FSlateColor(Bone))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(106.f, 618.f)).Size(FVector2D(560.f, 16.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("INTERSTELLAR RELAY  ·  CH.07")))
						.Font(TinyFont).ColorAndOpacity(FSlateColor(Mist))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Signal bars + readout.
					+ SCanvas::Slot().Position(FVector2D(1420.f, 594.f)).Size(FVector2D(100.f, 24.f))
					[
						SNew(SBox)
						[
							SNew(SCanvas)
							+ SCanvas::Slot().Position(FVector2D(0.f, 16.f)).Size(FVector2D(4.f, 6.f))
							[ SAssignNew(SignalBars[0], SImage).Image(WhiteBrush).ColorAndOpacity(Signal) ]
							+ SCanvas::Slot().Position(FVector2D(9.f, 13.f)).Size(FVector2D(4.f, 9.f))
							[ SAssignNew(SignalBars[1], SImage).Image(WhiteBrush).ColorAndOpacity(Signal) ]
							+ SCanvas::Slot().Position(FVector2D(18.f, 10.f)).Size(FVector2D(4.f, 12.f))
							[ SAssignNew(SignalBars[2], SImage).Image(WhiteBrush).ColorAndOpacity(Signal) ]
							+ SCanvas::Slot().Position(FVector2D(27.f, 6.f)).Size(FVector2D(4.f, 16.f))
							[ SAssignNew(SignalBars[3], SImage).Image(WhiteBrush).ColorAndOpacity(Signal) ]
							+ SCanvas::Slot().Position(FVector2D(36.f, 2.f)).Size(FVector2D(4.f, 20.f))
							[ SAssignNew(SignalBars[4], SImage).Image(WhiteBrush).ColorAndOpacity(Signal) ]
						]
					]
					+ SCanvas::Slot().Position(FVector2D(1478.f, 592.f)).Size(FVector2D(140.f, 16.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("SIGNAL 98%")))
						.Font(MetaFont).ColorAndOpacity(FSlateColor(Mist))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Close.
					+ SCanvas::Slot().Position(FVector2D(1812.f, 584.f)).Size(FVector2D(40.f, 40.f))
					[
						SAssignNew(CloseButton, SButton)
						.ButtonStyle(&CloseStyle)
						.ContentPadding(FMargin(0.f))
						.TouchMethod(EButtonTouchMethod::Down)
						.OnClicked(FOnClicked::CreateSP(this, &SSeerCommsPanel::HandleCloseClicked))
						[
							SNew(SBox).WidthOverride(40.f).HeightOverride(40.f)
							[
								SNew(SOverlay)
								+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
								[
									SNew(STextBlock).Text(FText::FromString(TEXT("×")))
									.Font(CtaFont).ColorAndOpacity(FSlateColor(Mist))
									.Visibility(EVisibility::SelfHitTestInvisible)
								]
							]
						]
					]

					// Portrait hologram.
					+ SCanvas::Slot().Position(FVector2D(60.f, 606.f)).Size(FVector2D(280.f, 280.f))
					[
						SAssignNew(PortraitGlow, SImage).Image(&GlowBrush)
						.ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.34f))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(85.f, 631.f)).Size(FVector2D(230.f, 230.f))
					[
						SAssignNew(RingDashImage, SImage).Image(&RingDashBrush)
						.ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.65f))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(105.f, 651.f)).Size(FVector2D(190.f, 190.f))
					[
						SAssignNew(RingImage, SImage).Image(&RingBrush)
						.ColorAndOpacity(FLinearColor(Halo.R, Halo.G, Halo.B, 0.55f))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(105.f, 624.f)).Size(FVector2D(190.f, 276.f))
					[
						SAssignNew(PortraitImage, SImage).Image(&PortraitBrush)
						.ColorAndOpacity(FLinearColor(0.92f, 1.0f, 1.0f, 1.0f))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Name block.
					+ SCanvas::Slot().Position(FVector2D(315.f, 632.f)).Size(FVector2D(320.f, 42.f))
					[
						SNew(STextBlock).Text(SpeakerName)
						.Font(NameFont).ColorAndOpacity(FSlateColor(Bone))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(316.f, 678.f)).Size(FVector2D(320.f, 16.f))
					[
						SNew(STextBlock).Text(SpeakerTag)
						.Font(SmallFont).ColorAndOpacity(FSlateColor(Mist))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(316.f, 702.f)).Size(FVector2D(8.f, 8.f))
					[
						SNew(SImage).Image(&GlowBrush).ColorAndOpacity(Signal)
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(330.f, 696.f)).Size(FVector2D(220.f, 20.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("在线 / ONLINE")))
						.Font(SmallFont).ColorAndOpacity(FSlateColor(Signal))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Live waveform.
					+ SCanvas::Slot().Position(FVector2D(316.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[0], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(328.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[1], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(340.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[2], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(352.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[3], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(364.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[4], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(376.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[5], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(388.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[6], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(400.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[7], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(412.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[8], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(424.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[9], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(436.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[10], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(448.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[11], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(460.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[12], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(472.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[13], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(484.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[14], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]
					+ SCanvas::Slot().Position(FVector2D(496.f, 726.f)).Size(FVector2D(4.f, 26.f))
					[ SAssignNew(WaveBars[15], SImage).Image(WhiteBrush).ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.75f)) ]

					+ SCanvas::Slot().Position(FVector2D(316.f, 760.f)).Size(FVector2D(420.f, 16.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("本条跃迁由 主播纽斯 赞助 · 单程票")))
						.Font(TinyFont).ColorAndOpacity(FSlateColor(Dim))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// ON AIR chip.
					+ SCanvas::Slot().Position(FVector2D(600.f, 632.f)).Size(FVector2D(8.f, 8.f))
					[
						SNew(SImage).Image(&GlowBrush).ColorAndOpacity(Alert)
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(614.f, 624.f)).Size(FVector2D(260.f, 20.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("直播中 / ON AIR")))
						.Font(SmallFont).ColorAndOpacity(FSlateColor(Mist))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Legibility plate behind the dialogue only.
					+ SCanvas::Slot().Position(FVector2D(584.f, 648.f)).Size(FVector2D(1216.f, 152.f))
					[
						SNew(SImage).Image(&TextScrimBrush).Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Dialogue (typewriter).
					+ SCanvas::Slot().Position(FVector2D(600.f, 656.f)).Size(FVector2D(1180.f, 140.f))
					[
						SAssignNew(BodyText, STextBlock)
						.Font(BodyFont)
						.ColorAndOpacity(FSlateColor(Bone))
						.AutoWrapText(true)
						.WrapTextAt(1180.f)
						.LineHeightPercentage(1.4f)
						.Justification(ETextJustify::Left)
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					+ SCanvas::Slot().Position(FVector2D(600.f, 800.f)).Size(FVector2D(700.f, 16.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("可用航线 / AVAILABLE ROUTE")))
						.Font(SmallFont).ColorAndOpacity(FSlateColor(Signal))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// The single route card.
					+ SCanvas::Slot().Position(FVector2D(600.f, 818.f)).Size(FVector2D(1210.f, 130.f))
					[
						SAssignNew(RouteButton, SButton)
						.ButtonStyle(&RouteStyle)
						.ContentPadding(FMargin(0.f))
						.TouchMethod(EButtonTouchMethod::Down)
						.OnClicked(FOnClicked::CreateSP(this, &SSeerCommsPanel::HandleRouteClicked))
						[
							SNew(SBox).WidthOverride(1210.f).HeightOverride(130.f)
							[
								SNew(SCanvas)
								+ SCanvas::Slot().Position(FVector2D(22.f, 28.f)).Size(FVector2D(74.f, 74.f))
								[
									SNew(SImage).Image(&PlanetBrush).Visibility(EVisibility::SelfHitTestInvisible)
								]
								+ SCanvas::Slot().Position(FVector2D(116.f, 12.f)).Size(FVector2D(560.f, 40.f))
								[
									SNew(STextBlock).Text(DestinationName)
									.Font(TitleFont).ColorAndOpacity(FSlateColor(Bone))
									.Visibility(EVisibility::SelfHitTestInvisible)
								]
								+ SCanvas::Slot().Position(FVector2D(118.f, 54.f)).Size(FVector2D(580.f, 16.f))
								[
									SNew(STextBlock).Text(DestinationMeta)
									.Font(MetaFont).ColorAndOpacity(FSlateColor(Mist))
									.Visibility(EVisibility::SelfHitTestInvisible)
								]
								+ SCanvas::Slot().Position(FVector2D(118.f, 78.f)).Size(FVector2D(300.f, 14.f))
								[
									SNew(STextBlock).Text(FText::FromString(TEXT("唯一航线 / ONLY ROUTE")))
									.Font(TinyFont).ColorAndOpacity(FSlateColor(Dim))
									.Visibility(EVisibility::SelfHitTestInvisible)
								]
								+ SCanvas::Slot().Position(FVector2D(910.f, 36.f)).Size(FVector2D(280.f, 58.f))
								[
									SNew(SOverlay)
									+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
									[
										SAssignNew(RouteGlow, SImage).Image(&GlowBrush)
										.ColorAndOpacity(FLinearColor(Amber.R, Amber.G, Amber.B, 0.f))
										.Visibility(EVisibility::SelfHitTestInvisible)
									]
									+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
									[
										SNew(SImage).Image(&PillBrush).Visibility(EVisibility::SelfHitTestInvisible)
									]
									+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
									[
										SAssignNew(CtaText, STextBlock).Text(CtaLabel)
										.Font(CtaFont).ColorAndOpacity(FSlateColor(Ink))
										.Visibility(EVisibility::SelfHitTestInvisible)
									]
									+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(FMargin(0.f, 0.f, 18.f, 2.f))
									[
										SAssignNew(ChevronText, STextBlock).Text(FText::FromString(TEXT("→")))
										.Font(CtaFont).ColorAndOpacity(FSlateColor(Ink))
										.Visibility(EVisibility::SelfHitTestInvisible)
									]
								]
							]
						]
					]

					// Idle manifest line (replaced by the status row while confirming).
					+ SCanvas::Slot().Position(FVector2D(600.f, 960.f)).Size(FVector2D(900.f, 16.f))
					[
						SAssignNew(IdleTexts[0], STextBlock)
						.Text(FText::FromString(TEXT("未解锁航线 / NO SIGNAL   ·   已加密 / ENCRYPTED")))
						.Font(TinyFont).ColorAndOpacity(FSlateColor(Dim))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]

					// Status / progress.
					+ SCanvas::Slot().Position(FVector2D(600.f, 954.f)).Size(FVector2D(1210.f, 46.f))
					[
						SAssignNew(StatusBox, SBox)
						.WidthOverride(1210.f).HeightOverride(46.f)
						.Visibility(EVisibility::Collapsed)
						[
							SNew(SOverlay)
							+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Top)
							[
								SNew(SBox).HeightOverride(22.f)
								[
									SAssignNew(StatusText, STextBlock)
									.Font(MetaFont).ColorAndOpacity(FSlateColor(AmberHi))
									.Visibility(EVisibility::SelfHitTestInvisible)
								]
							]
							+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Top).Padding(FMargin(0.f, 32.f, 0.f, 0.f))
							[
								SNew(SBox).HeightOverride(3.f)
								[
									SNew(SOverlay)
									+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
									[
										SNew(SImage).Image(WhiteBrush)
										.ColorAndOpacity(FLinearColor(Signal.R, Signal.G, Signal.B, 0.18f))
										.Visibility(EVisibility::SelfHitTestInvisible)
									]
									+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
									[
										SAssignNew(ProgressBar, SImage).Image(WhiteBrush)
										.ColorAndOpacity(Amber)
										.Visibility(EVisibility::SelfHitTestInvisible)
									]
								]
							]
						]
					]

					// Footer.
					+ SCanvas::Slot().Position(FVector2D(84.f, 1028.f)).Size(FVector2D(820.f, 16.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("UPLINK 3.2 TB/s  ·  LATENCY 042 ms  ·  ENCRYPTED")))
						.Font(TinyFont).ColorAndOpacity(FSlateColor(Dim))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
					+ SCanvas::Slot().Position(FVector2D(1570.f, 1024.f)).Size(FVector2D(290.f, 20.f))
					[
						SNew(STextBlock).Text(FText::FromString(TEXT("ENTER / F 确认     ESC 返回")))
						.Font(SmallFont).ColorAndOpacity(FSlateColor(Mist))
						.Visibility(EVisibility::SelfHitTestInvisible)
					]
				]
			]
		]
	];

	// Render-transform defaults used by the animations.
	if (ContentRoot.IsValid())
	{
		ContentRoot->SetRenderTransformPivot(FVector2D(0.5f, 1.0f));
	}
	for (TSharedPtr<SImage>& Bar : WaveBars)
	{
		if (Bar.IsValid())
		{
			Bar->SetRenderTransformPivot(FVector2D(0.5f, 1.f));
		}
	}
	for (TSharedPtr<SImage>& Bar : SignalBars)
	{
		if (Bar.IsValid())
		{
			Bar->SetRenderTransformPivot(FVector2D(0.5f, 1.f));
		}
	}
	if (ProgressBar.IsValid())
	{
		ProgressBar->SetRenderTransformPivot(FVector2D(0.f, 0.5f));
	}
	if (RouteGlow.IsValid())
	{
		RouteGlow->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
		RouteGlow->SetRenderTransform(FSlateRenderTransform(FScale2f(1.45f, 1.6f)));
	}
	if (RingImage.IsValid())
	{
		RingImage->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}
	if (RingDashImage.IsValid())
	{
		RingDashImage->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}
	if (PortraitImage.IsValid())
	{
		PortraitImage->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	}
	if (SweepImage.IsValid())
	{
		SweepImage->SetRenderTransformPivot(FVector2D(0.f, 0.f));
	}

	PlayIntro();
}

SSeerCommsPanel::~SSeerCommsPanel()
{
	// The pre-processor is registered with the Slate application, which keeps it
	// alive independently of this widget. Always unregister, even on teardown.
	if (InputProcessor.IsValid() && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().UnregisterInputPreProcessor(InputProcessor);
	}
}

UTexture2D* SSeerCommsPanel::LoadPortrait() const
{
	if (UTexture2D* Provided = PortraitTexture.Get())
	{
		return Provided;
	}
	return LoadObject<UTexture2D>(nullptr, TEXT("/Game/SeerLab/UI/Textures/T_AnchorNius_Portrait.T_AnchorNius_Portrait"));
}

void SSeerCommsPanel::PlayIntro()
{
	AnimTime = 0.f;
	CloseStart = 0.f;
	ConfirmStart = 0.f;
	StatusStart = 0.f;
	HoverAlpha = 0.f;
	TypingAccumulator = 0.f;
	VisibleChars = 0;
	bTyping = true;
	bConfirming = false;
	bConfirmFired = false;
	bStatusShown = false;
	bClosing = false;

	SetVisibility(EVisibility::Visible);
	if (BodyText.IsValid())
	{
		BodyText->SetText(FText::GetEmpty());
	}
	if (RouteButton.IsValid())
	{
		RouteButton->SetEnabled(true);
	}
	if (CtaText.IsValid())
	{
		CtaText->SetText(CtaLabel);
	}
	if (StatusBox.IsValid())
	{
		StatusBox->SetVisibility(EVisibility::Collapsed);
	}
	for (const TSharedPtr<SImage>& Widget : IdleRules)
	{
		if (Widget.IsValid())
		{
			Widget->SetVisibility(EVisibility::SelfHitTestInvisible);
		}
	}
	for (const TSharedPtr<STextBlock>& Widget : IdleTexts)
	{
		if (Widget.IsValid())
		{
			Widget->SetVisibility(EVisibility::SelfHitTestInvisible);
		}
	}
	if (ContentRoot.IsValid())
	{
		ContentRoot->SetRenderOpacity(0.f);
	}
	if (ScrimWidget.IsValid())
	{
		ScrimWidget->SetRenderOpacity(0.f);
	}
	RegisterInput();
}

void SSeerCommsPanel::RegisterInput()
{
	if (!InputProcessor.IsValid() && FSlateApplication::IsInitialized())
	{
		InputProcessor = MakeShared<FSeerDialogInputProcessor>();
		InputProcessor->Panel = SharedThis(this);
		FSlateApplication::Get().RegisterInputPreProcessor(InputProcessor, 0);
	}
}

void SSeerCommsPanel::UnregisterInput()
{
	if (InputProcessor.IsValid() && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().UnregisterInputPreProcessor(InputProcessor);
	}
	InputProcessor.Reset();
}

void SSeerCommsPanel::BeginClose()
{
	if (bClosing)
	{
		return;
	}
	bClosing = true;
	CloseStart = AnimTime;
}

void SSeerCommsPanel::ShowStatus(const FText& InStatus)
{
	if (bClosing)
	{
		return;
	}
	bConfirming = false;
	bStatusShown = true;
	StatusStart = AnimTime;
	if (StatusText.IsValid())
	{
		StatusText->SetText(InStatus);
	}
	if (StatusBox.IsValid())
	{
		StatusBox->SetVisibility(EVisibility::SelfHitTestInvisible);
	}
	for (const TSharedPtr<SImage>& Widget : IdleRules)
	{
		if (Widget.IsValid())
		{
			Widget->SetVisibility(EVisibility::Collapsed);
		}
	}
	for (const TSharedPtr<STextBlock>& Widget : IdleTexts)
	{
		if (Widget.IsValid())
		{
			Widget->SetVisibility(EVisibility::Collapsed);
		}
	}
	if (ProgressBar.IsValid())
	{
		ProgressBar->SetRenderOpacity(0.f);
	}
}

bool SSeerCommsPanel::HandleDialogKey(const FKey& Key)
{
	if (bClosing)
	{
		return true;
	}
	if (Key == EKeys::Escape)
	{
		BeginClose();
		return true;
	}
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::F
		|| Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		if (!bConfirming && !bStatusShown)
		{
			if (bTyping)
			{
				CompleteTyping();
			}
			else
			{
				ConfirmRoute();
			}
		}
		return true;
	}
	return false;
}

FReply SSeerCommsPanel::HandleCloseClicked()
{
	BeginClose();
	return FReply::Handled();
}

FReply SSeerCommsPanel::HandleRouteClicked()
{
	if (bClosing || bConfirming || bStatusShown)
	{
		return FReply::Handled();
	}
	if (bTyping)
	{
		CompleteTyping();
		return FReply::Handled();
	}
	ConfirmRoute();
	return FReply::Handled();
}

void SSeerCommsPanel::CompleteTyping()
{
	if (!bTyping)
	{
		return;
	}
	bTyping = false;
	VisibleChars = DialogueText.ToString().Len();
	RefreshVisibleText();
}

void SSeerCommsPanel::RefreshVisibleText()
{
	if (!BodyText.IsValid())
	{
		return;
	}
	const FString Full = DialogueText.ToString();
	const int32 Count = FMath::Clamp(VisibleChars, 0, Full.Len());
	BodyText->SetText(FText::FromString(Full.Left(Count)));
}

void SSeerCommsPanel::ConfirmRoute()
{
	if (bConfirming || bStatusShown || bClosing)
	{
		return;
	}
	bConfirming = true;
	bConfirmFired = false;
	ConfirmStart = AnimTime;
	if (RouteButton.IsValid())
	{
		RouteButton->SetEnabled(false);
	}
	if (CtaText.IsValid())
	{
		CtaText->SetText(FText::FromString(TEXT("跃迁准备中…")));
	}
	if (StatusText.IsValid())
	{
		StatusText->SetText(FText::FromString(TEXT("航线锁定：克罗斯星 · 正在建立跃迁通道…")));
	}
	if (StatusBox.IsValid())
	{
		StatusBox->SetVisibility(EVisibility::SelfHitTestInvisible);
	}
	for (const TSharedPtr<SImage>& Widget : IdleRules)
	{
		if (Widget.IsValid())
		{
			Widget->SetVisibility(EVisibility::Collapsed);
		}
	}
	for (const TSharedPtr<STextBlock>& Widget : IdleTexts)
	{
		if (Widget.IsValid())
		{
			Widget->SetVisibility(EVisibility::Collapsed);
		}
	}
}

void SSeerCommsPanel::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);
	AnimTime += InDeltaTime;
	UpdateAnimations(InDeltaTime, AllottedGeometry.GetLocalSize());
}

void SSeerCommsPanel::UpdateAnimations(float DeltaTime, const FVector2D& ViewSize)
{
	const float FitScale = FMath::Clamp(FMath::Min(ViewSize.X / 1920.f, ViewSize.Y / 1080.f), 0.05f, 4.f);

	// Entrance: 0.45s cubic-out fade + lift + slight scale.
	const float IntroT = FMath::Clamp(AnimTime / 0.45f, 0.f, 1.f);
	const float IntroE = 1.f - FMath::Pow(1.f - IntroT, 3.f);
	if (ContentRoot.IsValid())
	{
		ContentRoot->SetRenderOpacity(IntroE);
		ContentRoot->SetRenderTransform(FSlateRenderTransform(
			FScale2f(FitScale * FMath::Lerp(0.965f, 1.f, IntroE)),
			FVector2f(0.f, FMath::Lerp(26.f, 0.f, IntroE) * FitScale)));
	}
	if (ScrimWidget.IsValid())
	{
		ScrimWidget->SetRenderOpacity(IntroE);
	}

	// Typewriter with a longer beat after Chinese punctuation.
	if (bTyping && AnimTime > 0.28f && BodyText.IsValid())
	{
		const FString Full = DialogueText.ToString();
		TypingAccumulator += DeltaTime;
		constexpr float CharInterval = 0.033f;
		while (TypingAccumulator >= CharInterval && VisibleChars < Full.Len())
		{
			TypingAccumulator -= CharInterval;
			const TCHAR Ch = Full[VisibleChars];
			++VisibleChars;
			if (Ch == TEXT('，') || Ch == TEXT('。') || Ch == TEXT('！') || Ch == TEXT('？') || Ch == TEXT('…'))
			{
				TypingAccumulator -= 0.09f;
			}
		}
		RefreshVisibleText();
		if (VisibleChars >= Full.Len())
		{
			bTyping = false;
		}
	}

	// Idle life: breathing glow, pulsing live dot, rotating holo rings,
	// floating portrait, scrolling waveform and signal jitter.
	const float Idle = AnimTime;
	if (PortraitGlow.IsValid())
	{
		PortraitGlow->SetRenderOpacity(0.30f + 0.10f * FMath::Sin(Idle * 1.8f));
	}
	if (LiveDot.IsValid())
	{
		LiveDot->SetRenderOpacity(0.55f + 0.45f * (0.5f + 0.5f * FMath::Sin(Idle * 4.2f)));
	}
	if (RingImage.IsValid())
	{
		RingImage->SetRenderTransform(FSlateRenderTransform(FQuat2f(Idle * 0.18f)));
	}
	if (RingDashImage.IsValid())
	{
		RingDashImage->SetRenderTransform(FSlateRenderTransform(FQuat2f(-Idle * 0.42f)));
	}
	if (PortraitImage.IsValid())
	{
		PortraitImage->SetRenderTransform(FSlateRenderTransform(FVector2f(0.f, FMath::Sin(Idle * 1.25f) * 4.f)));
	}
	if (SweepImage.IsValid())
	{
		const float SweepT = FMath::Fmod(Idle, 4.2f) / 4.2f;
		SweepImage->SetRenderTransform(FSlateRenderTransform(FVector2f(0.f, SweepT * 432.f)));
		SweepImage->SetRenderOpacity(0.25f + 0.35f * FMath::Sin(SweepT * PI));
	}

	const float WaveAmplitude = bTyping ? 1.35f : 0.62f;
	for (int32 Index = 0; Index < WaveBars.Num(); ++Index)
	{
		if (WaveBars[Index].IsValid())
		{
			const float H = 0.22f + 0.78f * FMath::Abs(FMath::Sin(Idle * 3.1f + Index * 0.63f))
				* WaveAmplitude;
			WaveBars[Index]->SetRenderTransform(FSlateRenderTransform(FScale2f(1.f, FMath::Clamp(H, 0.12f, 1.f))));
		}
	}
	for (int32 Index = 0; Index < SignalBars.Num(); ++Index)
	{
		if (SignalBars[Index].IsValid())
		{
			const float H = 0.82f + 0.18f * FMath::Sin(Idle * 2.4f + Index * 0.9f);
			SignalBars[Index]->SetRenderTransform(FSlateRenderTransform(FScale2f(1.f, H)));
		}
	}

	// Hover treatment on the one route card.
	const bool bHovered = RouteButton.IsValid() && RouteButton->IsHovered();
	HoverAlpha = FMath::FInterpTo(HoverAlpha, (bHovered && !bConfirming && !bStatusShown) ? 1.f : 0.f, DeltaTime, 14.f);
	if (RouteGlow.IsValid())
	{
		const float Base = bConfirming ? 0.25f : 0.f;
		RouteGlow->SetRenderOpacity(Base + HoverAlpha * 0.35f);
		RouteGlow->SetColorAndOpacity(FLinearColor(Amber.R, Amber.G, Amber.B, 0.55f));
	}
	if (ChevronText.IsValid())
	{
		ChevronText->SetRenderTransform(FSlateRenderTransform(FVector2f(4.f * HoverAlpha, 0.f)));
	}

	// Confirmation progress.
	if (bConfirming)
	{
		const float T = FMath::Clamp((AnimTime - ConfirmStart) / 0.95f, 0.f, 1.f);
		if (ProgressBar.IsValid())
		{
			ProgressBar->SetRenderOpacity(1.f);
			ProgressBar->SetRenderTransform(FSlateRenderTransform(FScale2f(T, 1.f)));
		}
		if (T >= 1.f && !bConfirmFired)
		{
			bConfirmFired = true;
			OnTravelConfirmed.ExecuteIfBound();
		}
	}

	// Status auto-dismiss.
	if (bStatusShown && AnimTime - StatusStart > 2.4f && !bClosing)
	{
		BeginClose();
	}

	// Exit animation.
	if (bClosing)
	{
		const float CloseT = FMath::Clamp((AnimTime - CloseStart) / 0.28f, 0.f, 1.f);
		if (ContentRoot.IsValid())
		{
			ContentRoot->SetRenderOpacity(1.f - CloseT);
			ContentRoot->SetRenderTransform(FSlateRenderTransform(
				FScale2f(FitScale * FMath::Lerp(1.f, 0.975f, CloseT)),
				FVector2f(0.f, FMath::Lerp(0.f, 14.f, CloseT) * FitScale)));
		}
		if (ScrimWidget.IsValid())
		{
			ScrimWidget->SetRenderOpacity(1.f - CloseT);
		}
		if (CloseT >= 1.f)
		{
			UnregisterInput();
			OnClosed.ExecuteIfBound();
		}
	}
}
