# Generates assets\app.ico (PNG-framed icon: 16/32/48/64/128/256).
Add-Type -AssemblyName System.Drawing

$out = Join-Path $PSScriptRoot 'app.ico'
$sizes = @(16, 32, 48, 64, 128, 256)
$accent = [System.Drawing.Color]::FromArgb(255, 0xE4, 0x55, 0xE0)

$frames = @()
foreach ($s in $sizes) {
    $bmp = New-Object System.Drawing.Bitmap($s, $s, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'AntiAlias'
    $g.TextRenderingHint = 'AntiAlias'
    $g.Clear([System.Drawing.Color]::Transparent)

    $pad = [math]::Max(1, [int]($s * 0.08))
    $rect = New-Object System.Drawing.RectangleF($pad, $pad, ($s - 2 * $pad), ($s - 2 * $pad))
    $r = [float]($s * 0.18)
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $path.AddArc($rect.X, $rect.Y, $d, $d, 180, 90)
    $path.AddArc(($rect.Right - $d), $rect.Y, $d, $d, 270, 90)
    $path.AddArc(($rect.Right - $d), ($rect.Bottom - $d), $d, $d, 0, 90)
    $path.AddArc($rect.X, ($rect.Bottom - $d), $d, $d, 90, 90)
    $path.CloseFigure()

    $fill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(235, 0x14, 0x15, 0x18))
    $g.FillPath($fill, $path)
    $pen = New-Object System.Drawing.Pen($accent, [float][math]::Max(1, $s * 0.055))
    $g.DrawPath($pen, $path)

    $fontSize = [float]($s * 0.52)
    $font = New-Object System.Drawing.Font('Consolas', $fontSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = 'Center'
    $sf.LineAlignment = 'Center'
    $white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $g.DrawString('W', $font, $white, (New-Object System.Drawing.RectangleF(0, 0, $s, $s)), $sf)

    $g.Dispose()
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $frames += , @{ size = $s; data = $ms.ToArray() }
    $bmp.Dispose()
    $ms.Dispose()
}

$fs = [System.IO.File]::Create($out)
$bw = New-Object System.IO.BinaryWriter($fs)
$bw.Write([UInt16]0)                  # reserved
$bw.Write([UInt16]1)                  # type: icon
$bw.Write([UInt16]$frames.Count)

$offset = 6 + 16 * $frames.Count
foreach ($f in $frames) {
    $dim = if ($f.size -ge 256) { 0 } else { $f.size }
    $bw.Write([byte]$dim)             # width
    $bw.Write([byte]$dim)             # height
    $bw.Write([byte]0)                # palette
    $bw.Write([byte]0)                # reserved
    $bw.Write([UInt16]1)              # planes
    $bw.Write([UInt16]32)             # bpp
    $bw.Write([UInt32]$f.data.Length)
    $bw.Write([UInt32]$offset)
    $offset += $f.data.Length
}
foreach ($f in $frames) { $bw.Write($f.data) }
$bw.Flush()
$bw.Close()
$fs.Close()

Write-Output ("icon written: " + $out + " (" + (Get-Item $out).Length + " bytes)")
