<?php

declare(strict_types=1);

/**
 * Vygeneruje maintenance.html ze šablon chybové stránky Trenisu.
 *
 * Použití: php render-maintenance.php <trenis>/app/Modules/Presenters/templates/Error > maintenance.html
 *
 * Stránka slouží všem proxy hostům v NPM, proto má obecnou značku místo „Trenis“.
 */

$dir = $argv[1] ?? exit("Použití: php render-maintenance.php <adresář Error šablon Trenisu>\n");
$src = file_get_contents($dir . '/500.phtml');
if ($src === false || !preg_match('#^\t<style>.*?</style>#ms', $src, $m)) {
	exit("V {$dir}/500.phtml chybí blok <style>.\n");
}

$code = 503;
$title = 'Probíhá aktualizace';
$text = 'Nasazujeme novou verzi aplikace. Za chvilku jsme zpátky. Stránka se sama obnoví za 20 sekund.';
$hint = 'Nemusíte nic dělat. Když se stránka neobnoví sama, klikněte na Zkusit znovu.';
$actions = [['href' => '', 'label' => 'Zkusit znovu', 'variant' => 'primary']];
$headingLevel = 1;

ob_start();
require $dir . '/@errorBlock.phtml';
$block = str_replace('>Trenis</span>', '>PKP CARGO INTERNATIONAL</span>', (string) ob_get_clean());

echo <<<HTML
<!DOCTYPE html>
<!-- Stránka o údržbě pro NPM (502/503/504 z proxy). Layout převzatý z Trenisu: app/Modules/Presenters/templates/Error/500.phtml + @errorBlock.phtml. Generuje servery/npm/render-maintenance.php. -->
<html lang="cs">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta name="robots" content="noindex">
	<meta http-equiv="refresh" content="20">
	<title>Probíhá aktualizace</title>
	{$m[0]}
</head>
<body>
{$block}</body>
</html>

HTML;
